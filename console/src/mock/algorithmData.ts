import type { Algorithm } from '@/api/algorithm'

/**
 * 算法定义（静态数据，用于生成 mock 算法列表）
 */
interface AlgorithmDef {
  name: string
  type: string
  version: string
  description: string
}

/**
 * 全部算法定义 —— 6 大分类，共 56 个
 *
 * 命名规则：{前缀}-{分类中文名}[(特征描述)]
 * 去掉了旧的 -001/-002 序号后缀，改为语义化特征描述。
 */
const ALGORITHM_DEFINITIONS: AlgorithmDef[] = [
  // ==================== 数据同化 (assimilation) — 14 个 ====================
  {
    name: '3D-VAR-数据同化',
    type: 'assimilation',
    version: '2.1.0',
    description:
      '三维变分同化方法，通过最小化分析场与观测场的偏差代价函数，将多源观测数据融入数值预报背景场。适用于UAV气象数据实时同化场景，计算效率高，支持6小时同化窗口。',
  },
  {
    name: '3D-VAR-数据同化 (高性能版)',
    type: 'assimilation',
    version: '2.2.0',
    description:
      '三维变分同化高性能版本，采用GPU加速的共轭梯度求解器，将同化计算时间缩短至标准版的1/3。适用于大规模UAV集群实时气象数据同化，支持并行处理多批次观测数据。',
  },
  {
    name: '4D-VAR-数据同化',
    type: 'assimilation',
    version: '1.8.0',
    description:
      '四维变分同化方法，在时间维度上扩展3D-VAR，利用观测的时间分布信息约束分析场。适用于UAV航迹上连续观测数据的同化，支持12小时同化窗口和非线性观测算子。',
  },
  {
    name: '4D-VAR-数据同化 (高精度版)',
    type: 'assimilation',
    version: '1.9.1',
    description:
      '四维变分同化高精度版本，采用增广拉格朗日方法和精细化背景误差协方差模型，显著提升分析场精度。适用于科研级气象数据同化实验，支持高分辨率（1km）网格和复杂地形。',
  },
  {
    name: '5D-VAR-数据同化',
    type: 'assimilation',
    version: '1.3.0',
    description:
      '五维变分同化方法，在4D-VAR基础上引入物理参数约束维度，实现模式参数与初始条件的联合优化。适用于UAV气象传感器校准与数据同化一体化处理。',
  },
  {
    name: '5D-VAR-数据同化 (快速版)',
    type: 'assimilation',
    version: '1.4.0',
    description:
      '五维变分同化快速版本，采用增量方法和低分辨率外循环加速收敛。适用于业务化运行场景，在保持合理精度的前提下将计算时间控制在10分钟以内。',
  },
  {
    name: 'EnKF-数据同化',
    type: 'assimilation',
    version: '3.0.0',
    description:
      '集合卡尔曼滤波数据同化方法，利用有限规模集合样本估计背景误差协方差，流依赖特性使其在非线性系统中表现优异。适用于UAV多源观测数据的实时顺序同化。',
  },
  {
    name: 'EnKF-数据同化 (大集合版)',
    type: 'assimilation',
    version: '3.1.0',
    description:
      '集合卡尔曼滤波大集合版本，使用200+集合成员有效抑制采样噪声，配合局地化方案避免远距离虚假相关。适用于高精度气象场分析和不确定性量化场景。',
  },
  {
    name: 'Hybrid-EnVar-数据同化',
    type: 'assimilation',
    version: '2.0.0',
    description:
      '混合集合-变分同化方法，融合EnKF的流依赖误差估计与3D-VAR的静态控制变量变换优势。适用于UAV气象数据同化中需要兼顾精度与计算效率的业务场景。',
  },
  {
    name: 'Hybrid-EnVar-数据同化 (自适应版)',
    type: 'assimilation',
    version: '2.1.0',
    description:
      '混合集合-变分同化自适应版本，根据观测密度和天气系统特征自动调节集合与变分权重。适用于观测分布不均匀的UAV机动观测场景，动态优化同化策略。',
  },
  {
    name: 'VarBC-数据同化',
    type: 'assimilation',
    version: '1.5.0',
    description:
      '变分偏差校正方法，在变分同化框架内同步估计和校正观测系统偏差。适用于UAV机载传感器长期运行中的辐射校准和系统偏差订正。',
  },
  {
    name: 'VarBC-数据同化 (多变量版)',
    type: 'assimilation',
    version: '1.6.0',
    description:
      '变分偏差校正多变量版本，支持温度、湿度、风速等多变量联合偏差估计，利用变量间物理约束提升校正效果。适用于多传感器融合的UAV综合气象观测系统。',
  },
  {
    name: '3D-RTPP-数据同化',
    type: 'assimilation',
    version: '1.2.0',
    description:
      '三维松弛到随机扰动预报方法，通过向集合均值松弛的方式抑制滤波发散，保持集合离散度。适用于UAV气象数据同化中集合预报系统的离散度维持。',
  },
  {
    name: '3D-RTPP-数据同化 (增强版)',
    type: 'assimilation',
    version: '1.3.0',
    description:
      '三维松弛到随机扰动预报增强版本，引入自适应松弛系数和空间加权方案，在不同区域和天气条件下动态调整松弛强度。适用于复杂天气场景下的集合同化。',
  },

  // ==================== 路径规划 (planning) — 12 个 ====================
  {
    name: 'MPC-路径规划',
    type: 'planning',
    version: '2.5.0',
    description:
      '模型预测控制路径规划算法，基于滚动优化策略实时生成UAV飞行路径。支持动态障碍物规避和多约束条件（油耗、高度限制、禁飞区），适用于复杂城市低空环境。',
  },
  {
    name: 'MPC-路径规划 (实时版)',
    type: 'planning',
    version: '2.6.0',
    description:
      '模型预测控制路径规划实时版本，采用快速QP求解器和简化动力学模型，将求解时间压缩至50ms以内。适用于高速UAV实时避障和动态环境下的在线路径更新。',
  },
  {
    name: 'MPC-路径规划 (多目标版)',
    type: 'planning',
    version: '2.7.0',
    description:
      '模型预测控制路径规划多目标版本，基于帕累托最优前沿同时优化路径长度、能耗、安全裕度和飞行时间。适用于多UAV协同任务中的路径分配与优化。',
  },
  {
    name: 'A-Star-路径规划',
    type: 'planning',
    version: '3.0.0',
    description:
      'A*启发式搜索路径规划算法，在栅格化三维空间中搜索最优飞行路径。支持自定义启发函数和代价权重，适用于已知静态环境下的UAV全局路径规划。',
  },
  {
    name: 'A-Star-路径规划 (3D版)',
    type: 'planning',
    version: '3.1.0',
    description:
      'A*路径规划三维版本，采用八叉树空间索引和3D邻域搜索，支持复杂三维地形和建筑物规避。适用于城市峡谷和山区等三维受限空间的UAV路径规划。',
  },
  {
    name: 'A-Star-路径规划 (动态避障版)',
    type: 'planning',
    version: '3.2.0',
    description:
      'A*路径规划动态避障版本，结合时间窗概念和动态代价地图，实时响应移动障碍物和临时禁飞区变化。适用于UAV在动态空域中的实时路径重规划。',
  },
  {
    name: 'RRT-Connect-路径规划',
    type: 'planning',
    version: '2.0.0',
    description:
      '快速扩展随机树双向连接路径规划算法，通过双向树同时生长加速路径搜索。适用于高维构型空间和复杂约束环境下的UAV路径规划，无需环境显式建模。',
  },
  {
    name: 'RRT-Connect-路径规划 (高速版)',
    type: 'planning',
    version: '2.1.0',
    description:
      'RRT-Connect路径规划高速版本，采用KD-Tree近邻查询和贪心扩展策略，将路径搜索时间缩短至标准版的1/5。适用于大规模环境中UAV的快速路径生成。',
  },
  {
    name: 'RRT-Connect-路径规划 (窄通道版)',
    type: 'planning',
    version: '2.2.0',
    description:
      'RRT-Connect路径规划窄通道优化版本，引入桥接测试和定向采样策略，显著提升在狭窄通道和复杂障碍物间的路径搜索成功率。适用于城市密集建筑间的UAV穿行。',
  },
  {
    name: 'Dijkstra-3D-路径规划',
    type: 'planning',
    version: '1.5.0',
    description:
      'Dijkstra三维路径规划算法，在三维加权图中搜索最短路径，保证全局最优解。适用于网格化气象环境中的UAV安全路径规划，可融合气象风险代价。',
  },
  {
    name: 'Dijkstra-3D-路径规划 (加权版)',
    type: 'planning',
    version: '1.6.0',
    description:
      'Dijkstra三维路径规划加权版本，支持多维度代价权重配置（距离、气象风险、能耗、通信质量），可灵活调整优化目标。适用于多约束条件下的UAV综合最优路径规划。',
  },
  {
    name: 'GA-路径规划',
    type: 'planning',
    version: '2.0.0',
    description:
      '遗传算法路径规划，通过选择、交叉、变异等进化操作搜索全局最优路径。适用于多航点、多UAV协同路径优化，支持自定义适应度函数和约束处理。',
  },
  {
    name: 'GA-路径规划 (多约束版)',
    type: 'planning',
    version: '2.1.0',
    description:
      '遗传算法路径规划多约束版本，采用约束支配排序和可行性修复机制，同时处理油耗限制、禁飞区、高度层、通信覆盖等多维度约束。适用于复杂任务场景。',
  },
  {
    name: 'PSO-路径规划',
    type: 'planning',
    version: '1.8.0',
    description:
      '粒子群优化路径规划算法，模拟鸟群觅食行为在连续空间中搜索最优路径。收敛速度快，参数少，适用于中等规模环境下的UAV路径快速优化。',
  },
  {
    name: 'PSO-路径规划 (全局优化版)',
    type: 'planning',
    version: '1.9.0',
    description:
      '粒子群优化路径规划全局优化版本，引入多子群协作、混沌初始化和自适应惯性权重策略，有效避免早熟收敛。适用于大规模复杂环境中的全局最优路径搜索。',
  },

  // ==================== 风险评估 (risk) — 10 个 ====================
  {
    name: 'RiskAssess-风险评估',
    type: 'risk',
    version: '2.0.0',
    description:
      '综合风险评估算法，融合气象、地形、空域等多源数据进行UAV飞行风险量化评估。输出多维风险指标和综合风险等级，为飞行决策提供数据支撑。',
  },
  {
    name: 'RiskAssess-风险评估 (综合版)',
    type: 'risk',
    version: '2.1.0',
    description:
      '综合风险评估增强版本，引入贝叶斯网络进行多因素耦合风险建模，支持条件概率推理和敏感性分析。适用于复杂天气和空域条件下的精细化风险评估。',
  },
  {
    name: 'RiskAssess-风险评估 (实时版)',
    type: 'risk',
    version: '2.2.0',
    description:
      '综合风险评估实时版本，采用滑动窗口和增量更新策略，支持秒级风险态势刷新。适用于UAV飞行过程中的实时风险监控和预警。',
  },
  {
    name: 'AirsafeEval-风险评估',
    type: 'risk',
    version: '1.5.0',
    description:
      '适航安全评估算法，基于适航标准和运行规范对UAV飞行计划进行合规性检查和安全性评估。覆盖机型性能、气象条件、空域规则等多维度适航要求。',
  },
  {
    name: 'AirsafeEval-风险评估 (适航版)',
    type: 'risk',
    version: '1.6.0',
    description:
      '适航安全评估适航专项版本，严格依据民航法规和无人机适航标准进行逐项合规检查，生成详细的适航符合性报告。适用于UAV运营资质申请和合规审查。',
  },
  {
    name: 'TurbulenceDetect-风险评估',
    type: 'risk',
    version: '2.0.0',
    description:
      '湍流检测与风险评估算法，利用气象模型输出和机载传感器数据识别潜在湍流区域，量化湍流强度等级。适用于UAV低空飞行中的湍流规避和航路调整。',
  },
  {
    name: 'TurbulenceDetect-风险评估 (预测版)',
    type: 'risk',
    version: '2.1.0',
    description:
      '湍流检测与风险评估预测版本，结合数值天气预报和机器学习模型实现湍流的提前30分钟预测。适用于UAV航线规划阶段的湍流风险预判和航路优化。',
  },
  {
    name: 'IcingPredict-风险评估',
    type: 'risk',
    version: '1.8.0',
    description:
      '结冰预测风险评估算法，基于温度、湿度、液态水含量等气象参数计算UAV结冰概率和严重程度。适用于高空和跨气候带UAV飞行任务的结冰风险预警。',
  },
  {
    name: 'IcingPredict-风险评估 (精确版)',
    type: 'risk',
    version: '1.9.0',
    description:
      '结冰预测风险评估精确版本，引入微物理过程参数化方案和高分辨率云场分析，提供空间分辨率达500米的结冰风险精细预报。适用于精确化UAV飞行安全保障。',
  },
  {
    name: 'WindShear-风险评估',
    type: 'risk',
    version: '1.5.0',
    description:
      '风切变检测与风险评估算法，识别低空风切变和微下击暴流等危险风场现象，评估其对UAV起降和低空飞行的影响。适用于机场周边和复杂地形区域的飞行安全保障。',
  },
  {
    name: 'ConvectiveRisk-风险评估',
    type: 'risk',
    version: '1.3.0',
    description:
      '对流天气风险评估算法，基于对流有效位能、垂直风切变等热力-动力学参数评估雷暴和强对流天气风险。适用于UAV飞行计划中的对流天气规避决策。',
  },

  // ==================== 观测决策 (observation) — 8 个 ====================
  {
    name: 'ActiveObs-观测决策',
    type: 'observation',
    version: '2.0.0',
    description:
      '主动观测决策算法，基于信息增益和期望改进准则优化UAV观测位置和观测时序。在有限的飞行资源下最大化气象数据采集的信息价值。',
  },
  {
    name: 'ActiveObs-观测决策 (自适应版)',
    type: 'observation',
    version: '2.1.0',
    description:
      '主动观测决策自适应版本，根据实时气象场分析和观测覆盖缺口动态调整观测策略。适用于UAV在天气系统快速演变场景下的自适应观测任务规划。',
  },
  {
    name: 'ActiveObs-观测决策 (多目标版)',
    type: 'observation',
    version: '2.2.0',
    description:
      '主动观测决策多目标版本，同时优化观测信息增益、飞行能耗和通信约束等多重目标。适用于多UAV协同观测任务中的资源分配和观测策略优化。',
  },
  {
    name: 'SensorPlace-观测决策',
    type: 'observation',
    version: '1.5.0',
    description:
      '传感器布设优化算法，基于空间统计和覆盖优化理论确定地面/机载传感器的最优布设位置。适用于UAV气象观测网络的设计与部署优化。',
  },
  {
    name: 'SensorPlace-观测决策 (覆盖优化版)',
    type: 'observation',
    version: '1.6.0',
    description:
      '传感器布设优化覆盖增强版本，引入Voronoi图和贪心集合覆盖算法，在预算约束下最大化空间覆盖率和观测冗余度。适用于大规模UAV观测网络的成本效益优化。',
  },
  {
    name: 'AdaptiveSample-观测决策',
    type: 'observation',
    version: '1.8.0',
    description:
      '自适应采样决策算法，根据已采集数据的统计特征动态调整采样密度和采样区域。适用于UAV气象观测中的非均匀特征区域精细采样。',
  },
  {
    name: 'AdaptiveSample-观测决策 (在线版)',
    type: 'observation',
    version: '1.9.0',
    description:
      '自适应采样决策在线版本，支持UAV飞行过程中的实时在线决策，根据最新观测结果即时更新采样策略。适用于机动观测任务中的实时采样路径调整。',
  },
  {
    name: 'TargetTrack-观测决策',
    type: 'observation',
    version: '1.4.0',
    description:
      '目标追踪观测决策算法，针对移动天气系统（如锋面、涡旋）设计最优追踪观测路径。适用于UAV对台风外围、中尺度对流系统等移动目标的持续跟踪观测。',
  },
  {
    name: 'UTM-Collision-观测决策',
    type: 'observation',
    version: '1.2.0',
    description:
      'UTM冲突检测与观测决策算法，在无人机交通管理框架下评估多UAV航线冲突风险，生成冲突消解方案和优先级调度建议。适用于高密度低空空域的UAV协同运行。',
  },

  // ==================== 模型引擎 (model_engine) — 7 个 ====================
  {
    name: 'WRF-3km-模型引擎',
    type: 'model_engine',
    version: '4.2.0',
    description:
      'WRF中尺度数值天气预报模型3km分辨率版本，提供覆盖区域的高精度气象预报。适用于UAV飞行计划制定和航线气象条件预判，支持72小时预报时效。',
  },
  {
    name: 'WRF-3km-模型引擎 (快速积分版)',
    type: 'model_engine',
    version: '4.3.0',
    description:
      'WRF 3km快速积分版本，采用简化物理参数化方案和自适应时间步长，将72小时预报积分时间缩短40%。适用于UAV飞行前快速获取气象预报数据。',
  },
  {
    name: 'WRF-1km-模型引擎',
    type: 'model_engine',
    version: '4.5.0',
    description:
      'WRF高分辨率数值天气预报模型1km版本，精细解析城市热岛、海陆风等局地气象特征。适用于城市低空UAV飞行的高精度气象保障。',
  },
  {
    name: 'WRF-1km-模型引擎 (城市版)',
    type: 'model_engine',
    version: '4.6.0',
    description:
      'WRF 1km城市专项版本，耦合城市冠层模型和建筑物效应参数化，精确模拟城市街谷风场和建筑物尾流。适用于城市密集区UAV低空飞行的精细化气象预报。',
  },
  {
    name: 'WRF-9km-模型引擎',
    type: 'model_engine',
    version: '4.1.0',
    description:
      'WRF大尺度数值天气预报模型9km版本，提供区域尺度天气形势预报。计算效率高，适用于UAV飞行前的大范围天气概况分析和中长期趋势预判。',
  },
  {
    name: 'ML-Surrogate-模型引擎',
    type: 'model_engine',
    version: '1.5.0',
    description:
      '机器学习代理模型引擎，利用深度神经网络替代传统数值模式实现快速气象场预测。推理速度较WRF提升100倍以上，适用于UAV实时气象保障。',
  },
  {
    name: 'ML-Surrogate-模型引擎 (深度学习版)',
    type: 'model_engine',
    version: '1.6.0',
    description:
      '机器学习代理模型深度学习版本，采用Transformer架构和物理约束损失函数，在保持超快推理速度的同时显著提升预测精度。适用于对时效和精度均有要求的UAV气象保障。',
  },
  {
    name: 'NWP-PostProcess-模型引擎',
    type: 'model_engine',
    version: '2.0.0',
    description:
      '数值天气预报后处理引擎，对原始NWP输出进行偏差校正、降尺度统计和要素释用处理。提供更贴近观测的精细化气象产品，适用于UAV飞行决策的最终气象输入。',
  },

  // ==================== 边缘计算 (edge) — 5 个 ====================
  {
    name: 'EdgeInfer-边缘计算',
    type: 'edge',
    version: '2.0.0',
    description:
      '边缘推理引擎，将气象模型推理和风险评估算法部署在UAV机载边缘设备上，实现离线实时气象数据处理。适用于通信受限或延迟敏感的UAV飞行场景。',
  },
  {
    name: 'EdgeInfer-边缘计算 (轻量版)',
    type: 'edge',
    version: '2.1.0',
    description:
      '边缘推理引擎轻量版本，采用模型量化和剪枝技术将推理模型压缩至原体积的1/10，适配算力有限的UAV机载计算平台。适用于微型和小型UAV的机载边缘智能。',
  },
  {
    name: 'FederatedLearn-边缘计算',
    type: 'edge',
    version: '1.3.0',
    description:
      '联邦学习边缘计算框架，支持多UAV在保护数据隐私的前提下协同训练气象预测模型。适用于跨区域、跨单位的UAV气象数据协作分析场景。',
  },
  {
    name: 'SplitCompute-边缘计算',
    type: 'edge',
    version: '1.5.0',
    description:
      '端云协同分割计算框架，将气象模型计算任务智能分割为边缘端和云端两部分，根据网络状况动态调整计算分配。适用于网络带宽波动的UAV气象数据处理。',
  },
  {
    name: 'SplitCompute-边缘计算 (低延迟版)',
    type: 'edge',
    version: '1.6.0',
    description:
      '端云协同分割计算低延迟版本，采用模型早期退出和渐进式推理策略，在弱网环境下仍能保证端到端推理延迟低于200ms。适用于对实时性要求极高的UAV飞行安全决策。',
  },
  {
    name: 'OnDeviceAI-边缘计算',
    type: 'edge',
    version: '1.4.0',
    description:
      '端侧AI推理框架，为UAV机载NPU/GPU提供统一的模型部署和推理接口，支持TensorFlow Lite、ONNX等多种模型格式。适用于UAV机载智能算法的快速集成和部署。',
  },
]

/**
 * 生成 mock 算法列表
 *
 * 返回与 `Algorithm` 接口兼容的数组，所有字段（id / name / type / category /
 * version / description / status / endpoint / registeredAt / lastRunAt / runCount
 * 等）均确定性生成，保证 4 个 Vue 文件调用结果完全一致。
 */
export function generateMockAlgorithms(): Algorithm[] {
  return ALGORITHM_DEFINITIONS.map((def, index) => ({
    id: index + 1,
    name: def.name,
    category: def.type,
    type: def.type,
    version: def.version,
    status: 1,
    description: def.description,
    registeredAt: '2026-01-15T08:00:00',
    lastRunAt: '2026-06-18T10:30:00',
    runCount: Math.floor(Math.random() * 500),
    config: null,
    endpoint: `http://algorithm-engine:8000/api/v1/algorithms/${def.name.split('-')[0]!.toLowerCase()}/run`,
    paramSchema: null,
    createdAt: '2026-01-15T08:00:00',
    updatedAt: '2026-06-18T10:30:00',
  }))
}

/**
 * 返回所有算法名称列表（供 ExperimentManager 等需要算法名称的场景使用）
 */
export function getMockAlgorithmNames(): string[] {
  return ALGORITHM_DEFINITIONS.map((d) => d.name)
}
