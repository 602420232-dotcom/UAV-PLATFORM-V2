
╔══════════════════════════════════════════════════════════════════════════════╗
║              气象数据 → 无人机路径 一条龙 Input/Output/Return                ║
╚══════════════════════════════════════════════════════════════════════════════╝


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 0: 数据源 (CMA 天资/风雷 / FengWu GHR)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:   无 (定时触发, 每30min)

PROCESS: data_pipeline/fetcher.py
  CMAFetcher.fetch_tianzi() → HTTP请求 CMA API
  CMAFetcher.fetch_fenglei() → HTTP请求 CMA API
  (或模拟数据回退)

RETURN:
  xarray.Dataset {
    'u10': (lat, lon)  float32  10m 风速 u 分量 [m/s]
    'v10': (lat, lon)  float32  10m 风速 v 分量 [m/s]
    't2m': (lat, lon)  float32  2m 温度 [K]
    'rh2m':(lat, lon)  float32  2m 相对湿度 [%]
    'ps':  (lat, lon)  float32  地表气压 [Pa]
    'blh': (lat, lon)  float32  边界层高度 [m]
  }
  attrs: { 'source': 'tianzi'/'fenglei',
           'forecast_time': '2026-06-03T18:00:00' }



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 1: 时空配准 (Spatiotemporal Registration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  data_pipeline/registration.py
  sources: List[dict] = [
    {'name': 'tianzi',  'data': ndarray(6, 25, 25),  'resolution_km': 25},
    {'name': 'fenglei', 'data': ndarray(6, 50, 50),  'resolution_km': 3},
    {'name': 'fengwu',  'data': ndarray(6, 1, 1),    'resolution_km': 25},
  ]

PROCESS: SpatiotemporalRegistrator.register()
  1. 重采样到统一 3km 网格 (双线性插值)
  2. 地形校正 (温度/气压按 DEM 修正)
  3. 时间偏差加权 (最新数据权重最大)
  4. 加权叠加融合

RETURN:
  registered: ndarray(6, 50, 50)
    [0] u10    [1] v10    [2] t2m
    [3] rh2m   [4] ps     [5] blh
  统一在 3km 网格上, 成都平原 150km×150km


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 2: 异常值检测 (Outlier Detection)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  data_pipeline/outlier_detector.py:OutlierDetector.detect_and_fix()
  data: ndarray(6, 50, 50) — 时空配准后的气象场

PROCESS: OutlierDetector.detect(data) + fix(data, mask)
  1. 物理范围检查:
     - t2m ∈ [220K, 330K], 风速 ≤ 50m/s, ps ∈ [50kPa, 105kPa]
     - rh ∈ [0%, 100%], blh ∈ [0m, 3000m]
  2. 3σ 统计离群 (鲁棒 Z-score, 基于 M.A.D.)
  3. 空间一致性 (邻域 3×3 均值的 4σ 范围)
  4. 时序一致性 (相邻时次跳变 > 5σ)
  5. 异常值修复: 邻域均值填充 + 高斯平滑补全NaN

RETURN:
  cleaned: ndarray(6, 50, 50)  — 清洗后的气象场
  self.last_mask: ndarray(6, 50, 50) bool  — True=该点曾被标记为异常


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 3: 多模型动态融合 (Dynamic Weight Fusion)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  fusion/ensemble.py:DynamicWeightFusion.fuse()
  fields: Dict[str, Tensor] = {
    'fengwu_ghr': Tensor(1, 6, 50, 50),  — 风乌 全局背景
    'tianzi':     Tensor(1, 6, 50, 50),  — 天资 全球模式
    'fenglei':    Tensor(1, 6, 50, 50),  — 风雷 区域模式
  }

PROCESS: DynamicWeightFusion.fuse()
  1. 初始权重: 风乌 0.15 + 天资 0.25 + 风雷 0.60
  2. 各模型按其权重加权求和
  3. 不同分辨率自动双线性插值对齐
  4. 权重可自适应更新 (基于近期 RMSE)

PROCESS: PhysicsConstraint.forward(fused)
  1. t2m ≥ 180K;  ps ≥ 50000Pa
  2. rh2m ∈ [0%, 100%];  blh ≥ 50m

RETURN:
  fused: Tensor(1, 6, 50, 50)  — 物理约束后的融合场


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 4: CNN 空间订正 (Spatial Correction)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  cnn_corrector/model.py:CNNCorrector.forward()
  x:   Tensor(1, 11, 50, 50)  融合场 + 辅助通道
  dem: Tensor(1, 1, 50, 50)   DEM 高程

  x 通道含义:
    [0-5]  u10, v10, t2m, rh2m, ps, blh
    [6]    DEM 高程
    [7-10] 标准化辅助 (u10/10, t2m/300, ps/1000)

PROCESS:
  SpatialCorrector (浅层CNN)
    Conv3×3 → BN → ReLU → Dropout → Conv3×3 → BN → ReLU → Conv1×1
    残差连接 DEM 编码分支

  LSTMTemporalCorrector (ConvLSTM 时序)
    多帧输入 → ConvLSTM × 2 层 → 输出单帧

RETURN:
  corrected: Tensor(1, 6, 50, 50)
    订正后的 3km 网格场 (去除了系统偏差)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 5: 概率 U-Net 降尺度 (Probabilistic Downscaling)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  unet_downscaler/probabilistic.py:ProbabilisticUNet.forward()
  x:  Tensor(1, 6, 50, 50)  — CNN 订正后的 3km 场

PROCESS:
  U-Net Encoder: DoubleConv → Down × 4 → Bottleneck
  U-Net Decoder: Up × 4 → AttentionGate (可选观测同化)
  上采样: ConvTranspose × 3  (50→150, 3×)
  双头输出: mean_head + log_var_head

RETURN:
  mean:    Tensor(1, 6, 150, 150)  预报均值
             6ch: u10, v10, t2m, rh2m, ps, blh
             150×150 = 1km 分辨率, 成都平原

  log_var: Tensor(1, 6, 150, 150)  对数方差 (约束在 [-5, 5])
             exp(log_var) 得到方差 σ²
             σ 越大 = 该位置预报越不确定


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 6: EnKF 贝叶斯同化 (Ensemble Kalman Filter)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  gpr_risk/enkf.py:EnsembleKalmanFilter.assimilate()
  mean:    ndarray(6, 150, 150)  概率 U-Net 均值
  var:     ndarray(6, 150, 150)  概率 U-Net 方差
  observations:     ndarray(M,)  新观测值 (无人机回传/气象站)
  obs_positions:    ndarray(M, 2)  观测位置 (y, x)

PROCESS:
  1. generate_ensemble(mean, var) → 20个集合成员
     ensemble[i] = mean + noise × σ

  2. assimilate(ensemble, obs, pos):
     a. 计算集合均值 & 扰动矩阵 X'
     b. 观测算子 H: 网格 → 观测位置插值
     c. 卡尔曼增益: K = P^f H^T (H P^f H^T + R)^{-1}
     d. 每个成员: x^a_i = x^f_i + K(y - Hx^f_i)
     e. 协方差膨胀: × 1.05

RETURN:
  analysis:        ndarray(20, 6, 150, 150)  同化后集合
  analysis_mean:   ndarray(6, 150, 150)      同化后均值场
  analysis_variance: ndarray(6, 150, 150)    同化后方差 (↓ 下降了!)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 7: GPR 风险场 (Risk Variance Field)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  gpr_risk/model.py:GPRiskEstimator.fit() / risk_field()
  residual: Tensor(1, 6, 150, 150) – EnKF 同化后残差 (真值-预测)
  coords:   Tensor(N, 2)          – 格点坐标 (可选, 默认自动生成)

PROCESS:
  1. 展平残差 → (N,) 训练数据
  2. 拟合高斯过程 (GPyTorch):
     - 小数据量: ExactGP (RBF核)
     - 大数据量: SparseGP (500诱导点)
  3. 预测全场的方差场

RETURN:
  risk_map: Tensor(1, 150, 150)
    风险方差值, 0~1 归一化
    高值区域: 预报不确定性大 → 无人机风险高
    低值区域: 预报可信度高 → 可安全通行


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 8: 风险感知代价重构 (Risk-Aware Cost Function)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  path_planning/cost_function.py:RiskCostFunction.edge_cost()
  p1, p2:        (y, x) 格子坐标          — 边的两端
  wind_u:        ndarray(H, W) 风场 u    — 来自 EnKF 均值场
  wind_v:        ndarray(H, W) 风场 v
  risk_map:      ndarray(H, W) 风险方差    — 来自 GPR
  tke:           ndarray(H, W) 湍流动能   — 可选
  restricted_zones: ndarray(H, W) 禁飞区   — 可选
  precipitation: ndarray(H, W) 降水率     — 可选

PROCESS:  Cost = α·Met + β·Energy + γ·Dist + δ·Smooth + ε·Restricted

  Meteorological Cost (α=0.35):
    - 侧风分量 × 0.30
    - GPR 风险方差 × 0.20
    - 湍流强度 × 0.25
    - 热力 (垂直速度) × 0.15
    - 降水 × 0.10
    硬约束: 风速 > 12m/s → 代价 × 1e6

  Energy Cost (β=0.25):
    P = (mg + 0.5·ρ·Cd·A·(v+v_headwind)²) × v
    back to battery_capacity 归一化

  Distance Cost (γ=0.20): 欧氏距离
  Smoothness (δ=0.10):   路径曲率
  Restricted (ε=0.10):   禁飞区 → 1e6 惩罚

RETURN:
  total_cost: float
    从 p1 到 p2 的通行总代价
    越大 = 越不建议走这条边


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 9: 风险感知 A* 路径规划 (Risk-Aware A*)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  path_planning/planner.py:GPRPathPlanner.plan()
  risk_map: ndarray(150, 150)    — GPR 风险场
  wind_u:   ndarray(150, 150)    — 风场 u
  wind_v:   ndarray(150, 150)    — 风场 v
  start:    Tuple(float, float)  — 起点 (x, y) km
  end:      Tuple(float, float)  — 终点 (x, y) km

PROCESS:
  _risk_aware_astar(risk, u, v, start, end):
    f = g_distance + h + λ·risk  + μ·逆风惩罚
    8 方向邻域搜索
    禁飞区 (risk > 0.9) 标记为不可达
    找不到路径时回退到直线

  _bezier_smooth(path):
    3 阶贝塞尔曲线平滑

RETURN:
  waypoints: List[Waypoint] 路径航点列表
    Waypoint(
      x: float      — km, 相对成都中心
      y: float      — km
      z: float      — 高度 m (默认 100)
      risk: float   — 该点风险值 0~1
      wind_u: float — 该点风场 u [m/s]
      wind_v: float — 该点风场 v [m/s]
    )


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 10: MPC 滚动时域优化 (Model Predictive Control)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  control/mpc.py:ModelPredictiveController
  init(uav: UAVState, goal: Tuple)
    UAVState(x, y, z, vx, vy, heading, battery, status)

  loop(risk_map, wind_u, wind_v, tke, restricted, precip)
    每 10 分钟调用一次, 环境场随时间更新

PROCESS:
  1. _check_termination():
     - 到达终点? → REACHED
     - 电量 < 20%?  → EMERGENCY
     - 进入禁飞区?  → EMERGENCY
     - 迭代 > 100?  → FAILED

  2. _predict_environment(horizon=6):
     用持续性衰减假设预测未来 N 步:
       risk_{t+n} = risk_t × w^n + mean × (1-w^n)

  3. _predict_states(horizon):
     匀速外推 N 步后的位置 x_{t+n}

  4. _optimize_trajectory(horizon):
     对每步: 在预测风险场上 A* 规划子路径
     只执行第一步, 下个时间步重复

RETURN:
  MPCTrajectory(
    waypoints: List[Waypoint]    — 未来 N 步路径
    costs:     List[float]       — 每步代价
    total_cost: float            — 总代价
    expected_arrival_s: float    — 预计到达时间 (s)
    risk_profile: List[float]    — 每步风险值
  )

  UAVState 更新:
    x, y → 第一步的目标位置
    vx, vy → 朝向目标的速度分量
    battery -= 0.01
    status → EXECUTING / REACHED / FAILED / EMERGENCY


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 11: 贝叶斯主动观测决策 (Bayesian Active Observation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  active_obs/bayesian_observer.py:BayesianActiveObserver
  variance_map: ndarray(150, 150)  — GPR/EnKF 方差场
  existing_sites: List[(x, y)]     — 已有观测站位置

PROCESS:
  1. 生成候选点 (间隔 3km)
  2. 排除已有站点附近 (2km 内)
  3. 按采集函数排序:
     - 'variance' (默认): 方差最大
     - 'entropy': 信息熵最大
     - 'mutual_info': 方差 + 多样性
  4. 从 top 中挑分散的 N 个点
  5. update_gpr(): 同化新观测到 sklearn GPR

RETURN:
  query_points: List[(x, y)]
    建议无人机去采集的 N 个位置
    每个 (x, y) 以成都中心为原点, 单位 km

  内部更新:
    self.sampled_positions += query_points
    self.sampled_values += observations
    self.gpr_model.fit(X, y)  — GPR 重新训练


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 12: 多机冲突消解 (Multi-UAV Conflict Resolution)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  multi_uav/conflict_resolver.py:MultiUAVConflictResolver
  agents: List[UAVAgent]
    UAVAgent(id, priority, x, y, z, speed, heading, path)

PROCESS:
  1. detect_conflicts(agents):
     对每对无人机:
       - 水平距离 < 200m?  垂直 < 30m?
       - 碰撞时间 < 60s?
      → 按紧迫程度排序

  2. resolve(agents, conflicts):
     优先级: 方法1 → 方法2 → 方法3
     a. 高度层分离 (50m 间隔)
     b. 速度调节 (低优先级减速 5m/s)
     c. 航向偏移 (向右 15°)

  3. maintain_formation(agents, 'line'/'triangle'):
     编队保持 (一字纵队 / 三角队形)

RETURN:
  adjusted_agents: List[UAVAgent]
    高度/速度/航向调整后的无人机列表
    无冲突的安全轨迹


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段 13: MAVLink 输出 (PX4/ArduPilot)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT:  path_planning/mavlink_output.py:export_to_mavlink()
  waypoints:  List[Waypoint]  来自 GPRPathPlanner 或 MPC
  output_type: 'plan' | 'mavlink'
  speed:      float           巡航速度 m/s
  home:       (lat, lon, alt) 起飞点

PROCESS:
  GeoConverter.local_to_geo(x_km, y_km, alt_m):
    lat = ref_lat + y × 0.0090
    lon = ref_lon + x × 0.0097

  MissionPlanGenerator.generate_plan():
    → QGC .plan JSON:
      HOME → TAKEOFF → WAYPOINT... → TARGET → RTL

  MAVLinkEncoder:
    goto_waypoint(lat, lon, alt, speed)  → COMMAND_LONG (#76)
    rtl()                                 → NAV_RETURN_TO_LAUNCH
    heartbeat(armed)                      → HEARTBEAT (#0)

RETURN:
  output_type='plan':
    str (JSON)  — 可直接保存为 .plan 文件, QGC 导入

  output_type='mavlink':
    str (hex)   — MAVLink v2 帧序列, 串口/UDP 发送

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
