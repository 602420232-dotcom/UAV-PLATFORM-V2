import { get, post } from './request'

/** 数据库信息 */
export interface DatabaseInfo {
  name: string
  sizeMb: number
  tableCount: number
}

/** 表信息 */
export interface TableInfo {
  name: string
  comment?: string
  rows: number
  columns: number
  engine: string
  createTime: string
}

/** 列信息 */
export interface ColumnInfo {
  name: string
  type: string
  nullable: string
  key: string
  default: unknown
  comment?: string
}

/** SQL 查询结果 */
export interface QueryResult {
  columns: string[]
  rows: Record<string, unknown>[]
  total: number
  affectedRows?: number
  message?: string
}

/** 表数据分页结果 */
export interface TableDataResult {
  rows: Record<string, unknown>[]
  total: number
  page: number
  size: number
}

/** 数据库管理 API */
export const databaseApi = {
  /** 获取数据库列表 */
  getDatabases(): Promise<DatabaseInfo[]> {
    return get<DatabaseInfo[]>('/v1/database/list')
  },

  /** 获取表列表 */
  getTables(database?: string): Promise<TableInfo[]> {
    return get<TableInfo[]>('/v1/database/tables', { database })
  },

  /** 获取表列信息 */
  getTableColumns(database: string, table: string): Promise<ColumnInfo[]> {
    return get<ColumnInfo[]>('/v1/database/tables/columns', { database, table })
  },

  /** 执行 SQL 查询 */
  executeQuery(data: { sql: string; database?: string }): Promise<QueryResult> {
    return post<QueryResult>('/v1/database/query', data)
  },

  /** 获取表数据（分页） */
  getTableData(database: string, table: string, params?: { page?: number; size?: number }): Promise<TableDataResult> {
    return get<TableDataResult>('/v1/database/tables/data', { database, table, ...params })
  },
}
