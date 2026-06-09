<template>
  <div class="parameter-tuning">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <div class="top-bar-left">
        <h2 class="page-title">算法参数调优</h2>
        <el-tag type="warning" effect="plain" size="default" class="demo-tag">
          <el-icon><MagicStick /></el-icon>&nbsp;演示模式 · 参数调优为本地模拟
        </el-tag>
      </div>

      <div class="top-bar-controls">
        <el-button type="primary" plain @click="loadTemplates">
          <el-icon><FolderOpened /></el-icon>&nbsp;加载模板
        </el-button>
        <el-button type="default" @click="loadDefaults">
          <el-icon><RefreshLeft /></el-icon>&nbsp;加载默认参数
        </el-button>
        <el-button type="warning" @click="openSaveTemplate">
          <el-icon><CollectionTag /></el-icon>&nbsp;保存为模板
        </el-button>
        <el-button type="success" :loading="running" @click="startTuning">
          <el-icon><VideoPlay /></el-icon>&nbsp;{{ running ? '调优中…' : '开始调参 / 运行' }}
        </el-button>
        <el-button type="primary" @click="exportJSON">
          <el-icon><Download /></el-icon>&nbsp;导出 JSON 配置
        </el-button>
      </div>
    </div>

    <!-- 算法选择下拉框 -->
    <div class="algo-select-container">
      <div class="algo-select-label">
        <el-icon><Cpu /></el-icon>
        <span>选择算法</span>
      </div>
      <el-select 
        v-model="activeAlgo" 
        class="algo-select"
        placeholder="请选择算法"
        filterable
        clearable
        size="large"
      >
        <el-option-group label="路径规划">
          <el-option label="VRPTW · 车辆路径问题" value="vrptw" />
          <el-option label="DE-RRT* · 差分进化路径规划" value="de-rrt-star" />
          <el-option label="DWA · 动态窗口法" value="dwa" />
        </el-option-group>
        <el-option-group label="机器学习">
          <el-option label="ConvLSTM · 卷积长短期记忆网络" value="convlstm" />
          <el-option label="XGBoost · 极端梯度提升" value="xgboost" />
          <el-option label="GPR · 高斯过程回归" value="gpr" />
          <el-option label="CNN · 卷积神经网络" value="cnn" />
          <el-option label="U-Net · 语义分割网络" value="unet" />
        </el-option-group>
        <el-option-group label="数据同化">
          <el-option label="3DVAR · 三维变分同化" value="three-d-var" />
          <el-option label="4DVAR · 四维变分同化" value="four-d-var" />
          <el-option label="5DVAR · 五维变分同化" value="five-d-var" />
          <el-option label="EnKF · 集合卡尔曼滤波" value="enkf" />
        </el-option-group>
      </el-select>
    </div>

    <!-- 主体：左 35% / 右 65% -->
    <div class="main-body">
      <!-- 左侧 · 参数配置面板 -->
      <div class="left-panel">
        <el-card shadow="never" class="params-card">
          <template #header>
            <div class="panel-title">
              <el-icon><Tools /></el-icon>&nbsp;
              <el-tag :type="algoMeta[activeAlgo].tagType" size="default" effect="dark">
                {{ algoMeta[activeAlgo].label }}
              </el-tag>
              <span class="panel-sub">参数配置</span>
            </div>
          </template>

          <!-- 通用参数 -->
          <div class="section-block">
            <div class="section-title">通用参数</div>

            <el-form label-position="top" size="default" class="params-form">
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="最大迭代次数 (maxIterations)">
                    <el-input-number
                      v-model="commonParams.maxIterations"
                      :min="10"
                      :max="100000"
                      :step="10"
                      controls-position="right"
                      style="width: 100%"
                    />
                    <div class="help-text">算法最大迭代次数上限，达到后强制终止</div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="时间限制 (timeLimitSec)">
                    <el-input-number
                      v-model="commonParams.timeLimitSec"
                      :min="1"
                      :max="3600"
                      :step="1"
                      controls-position="right"
                      style="width: 100%"
                    />
                    <div class="help-text">单次运行最长时间（秒），超时即停止</div>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="随机种子 (randomSeed)">
                <el-input-number
                  v-model="commonParams.randomSeed"
                  :min="0"
                  :max="2147483647"
                  :step="1"
                  controls-position="right"
                  style="width: 100%"
                />
                <div class="help-text">固定种子可复现实验结果；0 表示使用系统时间</div>
              </el-form-item>
            </el-form>
          </div>

          <el-divider />

          <!-- 算法专用参数 -->
          <div class="section-block">
            <div class="section-title">{{ algoMeta[activeAlgo].label }} · 专用参数</div>

            <!-- VRPTW -->
            <div v-if="activeAlgo === 'vrptw'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="车辆数量 (vehicleCount)">
                      <el-slider v-model="params.vrptw.vehicleCount" :min="1" :max="50" :step="1" show-input />
                      <div class="help-text">可用车辆总数</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="车辆容量 (capacity)">
                      <el-slider v-model="params.vrptw.capacity" :min="10" :max="500" :step="10" show-input />
                      <div class="help-text">每辆车的最大负载容量</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="硬时间窗约束 (timeWindowHard)">
                  <el-switch v-model="params.vrptw.timeWindowHard" active-text="启用" inactive-text="禁用" />
                  <div class="help-text">启用后不允许违反时间窗约束</div>
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="延误惩罚系数 (penaltyDelay)">
                      <el-slider v-model="params.vrptw.penaltyDelay" :min="1" :max="500" :step="10" show-input />
                      <div class="help-text">超出时间窗的惩罚权重</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="提前惩罚系数 (penaltyEarly)">
                      <el-slider v-model="params.vrptw.penaltyEarly" :min="1" :max="100" :step="5" show-input />
                      <div class="help-text">提前到达的惩罚权重</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="最大路径数 (maxRoutes)">
                  <el-slider v-model="params.vrptw.maxRoutes" :min="5" :max="200" :step="5" show-input />
                  <div class="help-text">算法生成的最大路径数量限制</div>
                </el-form-item>
              </el-form>
            </div>

            <!-- DE-RRT* -->
            <div v-else-if="activeAlgo === 'de-rrt-star'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="种群大小 (popSize)">
                      <el-slider v-model="params.deRrtStar.popSize" :min="50" :max="500" :step="10" show-input />
                      <div class="help-text">每代差分进化的样本数量，越大搜索越全面但越慢</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="最大迭代 (maxIter)">
                      <el-slider v-model="params.deRrtStar.maxIter" :min="100" :max="10000" :step="50" show-input />
                      <div class="help-text">DE 内部迭代上限</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="步长 (stepSize)">
                      <el-input-number
                        v-model="params.deRrtStar.stepSize"
                        :min="0.1" :max="5" :step="0.1" :precision="2"
                        controls-position="right" style="width: 100%"
                      />
                      <div class="help-text">RRT 扩展步长（米）</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="目标半径 (goalRadius)">
                      <el-input-number
                        v-model="params.deRrtStar.goalRadius"
                        :min="0.5" :max="10" :step="0.5" :precision="2"
                        controls-position="right" style="width: 100%"
                      />
                      <div class="help-text">进入目标区域的判定半径（米）</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="精英保留比例 (elitism)">
                      <el-slider v-model="params.deRrtStar.elitism" :min="0.1" :max="0.5" :step="0.05" show-input />
                      <div class="help-text">每代直接保留的精英个体比例</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="变异概率 (mutationRate)">
                      <el-slider v-model="params.deRrtStar.mutationRate" :min="0.01" :max="0.3" :step="0.01" show-input />
                      <div class="help-text">DE 变异操作的概率</div>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>

            <!-- DWA -->
            <div v-else-if="activeAlgo === 'dwa'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="最小速度 vMin (m/s)">
                      <el-input-number
                        v-model="params.dwa.vMin"
                        :min="0" :max="5" :step="0.1" :precision="2"
                        controls-position="right" style="width: 100%"
                      />
                      <div class="help-text">速度窗口下限</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="最大速度 vMax (m/s)">
                      <el-input-number
                        v-model="params.dwa.vMax"
                        :min="0.5" :max="20" :step="0.1" :precision="2"
                        controls-position="right" style="width: 100%"
                      />
                      <div class="help-text">速度窗口上限</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="最小角速度 omegaMin (rad/s)">
                      <el-input-number
                        v-model="params.dwa.omegaMin"
                        :min="-3.14" :max="0" :step="0.1" :precision="2"
                        controls-position="right" style="width: 100%"
                      />
                      <div class="help-text">角速度窗口下限（负值表示左转）</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="最大角速度 omegaMax (rad/s)">
                      <el-input-number
                        v-model="params.dwa.omegaMax"
                        :min="0" :max="3.14" :step="0.1" :precision="2"
                        controls-position="right" style="width: 100%"
                      />
                      <div class="help-text">角速度窗口上限（正值表示右转）</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="预测时间步 dtPred (s)">
                  <el-slider v-model="params.dwa.dtPred" :min="0.05" :max="0.5" :step="0.01" :precision="2" show-input />
                  <div class="help-text">每个速度采样的前向模拟时间步长</div>
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="8">
                    <el-form-item label="目标权重 alpha">
                      <el-slider v-model="params.dwa.alphaGain" :min="0.5" :max="5" :step="0.1" :precision="2" show-input />
                      <div class="help-text">朝向目标得分的权重</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="避障权重 beta">
                      <el-slider v-model="params.dwa.betaGain" :min="0.5" :max="10" :step="0.1" :precision="2" show-input />
                      <div class="help-text">远离障碍物得分的权重</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="速度权重 gamma">
                      <el-slider v-model="params.dwa.gammaGain" :min="0.5" :max="5" :step="0.1" :precision="2" show-input />
                      <div class="help-text">鼓励前进速度的权重</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="模拟采样次数 samples">
                  <el-slider v-model="params.dwa.samples" :min="10" :max="100" :step="1" show-input />
                  <div class="help-text">每个时间窗口内对 (v, omega) 的采样数量</div>
                </el-form-item>
              </el-form>
            </div>

            <!-- ConvLSTM -->
            <div v-else-if="activeAlgo === 'convlstm'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="隐藏层维度 (hiddenDim)">
                      <el-slider v-model="params.convlstm.hiddenDim" :min="16" :max="256" :step="16" show-input />
                      <div class="help-text">LSTM隐藏层特征维度</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="层数 (numLayers)">
                      <el-slider v-model="params.convlstm.numLayers" :min="1" :max="8" :step="1" show-input />
                      <div class="help-text">LSTM堆叠层数</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="序列长度 (seqLen)">
                      <el-slider v-model="params.convlstm.seqLen" :min="6" :max="96" :step="6" show-input />
                      <div class="help-text">时间序列输入长度</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Dropout (dropout)">
                      <el-slider v-model="params.convlstm.dropout" :min="0" :max="0.5" :step="0.05" :precision="2" show-input />
                      <div class="help-text">Dropout正则化概率</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="学习率 (learningRate)">
                      <el-slider v-model="params.convlstm.learningRate" :min="0.0001" :max="0.01" :step="0.0001" :precision="4" show-input />
                      <div class="help-text">优化器学习率</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="批次大小 (batchSize)">
                      <el-slider v-model="params.convlstm.batchSize" :min="8" :max="128" :step="8" show-input />
                      <div class="help-text">训练批次大小</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="训练轮数 (epochs)">
                  <el-slider v-model="params.convlstm.epochs" :min="10" :max="200" :step="10" show-input />
                  <div class="help-text">训练轮数</div>
                </el-form-item>
              </el-form>
            </div>

            <!-- XGBoost -->
            <div v-else-if="activeAlgo === 'xgboost'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="最大深度 (maxDepth)">
                      <el-slider v-model="params.xgboost.maxDepth" :min="1" :max="20" :step="1" show-input />
                      <div class="help-text">决策树最大深度</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="学习率 (learningRate)">
                      <el-slider v-model="params.xgboost.learningRate" :min="0.01" :max="0.3" :step="0.01" :precision="2" show-input />
                      <div class="help-text">每棵树的学习率</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="树数量 (nEstimators)">
                  <el-slider v-model="params.xgboost.nEstimators" :min="50" :max="1000" :step="50" show-input />
                  <div class="help-text">集成树的数量</div>
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="子采样比例 (subsample)">
                      <el-slider v-model="params.xgboost.subsample" :min="0.5" :max="1" :step="0.05" :precision="2" show-input />
                      <div class="help-text">每棵树使用的数据比例</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="特征采样比例 (colsampleByTree)">
                      <el-slider v-model="params.xgboost.colsampleByTree" :min="0.5" :max="1" :step="0.05" :precision="2" show-input />
                      <div class="help-text">每棵树使用的特征比例</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="L1正则化 (regAlpha)">
                      <el-slider v-model="params.xgboost.regAlpha" :min="0" :max="10" :step="0.1" :precision="2" show-input />
                      <div class="help-text">L1正则化系数</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="L2正则化 (regLambda)">
                      <el-slider v-model="params.xgboost.regLambda" :min="0" :max="10" :step="0.1" :precision="2" show-input />
                      <div class="help-text">L2正则化系数</div>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>

            <!-- CNN -->
            <div v-else-if="activeAlgo === 'cnn'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="卷积核数量 (filters)">
                      <el-slider v-model="params.cnn.filters" :min="16" :max="256" :step="16" show-input />
                      <div class="help-text">卷积层输出通道数</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="卷积核大小 (kernelSize)">
                      <el-slider v-model="params.cnn.kernelSize" :min="1" :max="7" :step="1" show-input />
                      <div class="help-text">卷积核尺寸</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="步长 (strides)">
                      <el-slider v-model="params.cnn.strides" :min="1" :max="3" :step="1" show-input />
                      <div class="help-text">卷积步长</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="填充方式 (padding)">
                      <el-select v-model="params.cnn.padding" style="width: 100%">
                        <el-option label="Same (保持尺寸)" value="same" />
                        <el-option label="Valid (不填充)" value="valid" />
                      </el-select>
                      <div class="help-text">卷积填充策略</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="激活函数 (activation)">
                      <el-select v-model="params.cnn.activation" style="width: 100%">
                        <el-option label="ReLU" value="relu" />
                        <el-option label="Leaky ReLU" value="leaky_relu" />
                        <el-option label="Sigmoid" value="sigmoid" />
                        <el-option label="Tanh" value="tanh" />
                      </el-select>
                      <div class="help-text">激活函数类型</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Dropout (dropout)">
                      <el-slider v-model="params.cnn.dropout" :min="0" :max="0.5" :step="0.05" :precision="2" show-input />
                      <div class="help-text">Dropout正则化概率</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="学习率 (learningRate)">
                      <el-slider v-model="params.cnn.learningRate" :min="0.0001" :max="0.01" :step="0.0001" :precision="4" show-input />
                      <div class="help-text">优化器学习率</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="训练轮数 (epochs)">
                      <el-slider v-model="params.cnn.epochs" :min="10" :max="100" :step="5" show-input />
                      <div class="help-text">训练轮数</div>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>

            <!-- U-Net -->
            <div v-else-if="activeAlgo === 'unet'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="基础通道数 (baseFilters)">
                      <el-slider v-model="params.unet.baseFilters" :min="16" :max="256" :step="16" show-input />
                      <div class="help-text">U-Net编码器第一层通道数</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="网络深度 (depth)">
                      <el-slider v-model="params.unet.depth" :min="2" :max="6" :step="1" show-input />
                      <div class="help-text">编码器/解码器层数</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="激活函数 (activation)">
                      <el-select v-model="params.unet.activation" style="width: 100%">
                        <el-option label="ReLU" value="relu" />
                        <el-option label="Leaky ReLU" value="leaky_relu" />
                        <el-option label="GELU" value="gelu" />
                      </el-select>
                      <div class="help-text">激活函数类型</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Dropout (dropout)">
                      <el-slider v-model="params.unet.dropout" :min="0" :max="0.5" :step="0.05" :precision="2" show-input />
                      <div class="help-text">Dropout正则化概率</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="学习率 (learningRate)">
                      <el-slider v-model="params.unet.learningRate" :min="0.00001" :max="0.001" :step="0.00001" :precision="5" show-input />
                      <div class="help-text">优化器学习率</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="训练轮数 (epochs)">
                      <el-slider v-model="params.unet.epochs" :min="10" :max="100" :step="5" show-input />
                      <div class="help-text">训练轮数</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="损失函数 (loss)">
                  <el-select v-model="params.unet.loss" style="width: 100%">
                    <el-option label="均方误差 (MSE)" value="mse" />
                    <el-option label="平均绝对误差 (MAE)" value="mae" />
                    <el-option label="Dice Loss" value="dice" />
                    <el-option label="交叉熵 (Cross-Entropy)" value="cross_entropy" />
                  </el-select>
                  <div class="help-text">损失函数类型</div>
                </el-form-item>
              </el-form>
            </div>

            <!-- GPR -->
            <div v-else-if="activeAlgo === 'gpr'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="核函数 kernel">
                      <el-select v-model="params.gpr.kernel" style="width: 100%">
                        <el-option label="RBF (高斯径向基)" value="RBF" />
                        <el-option label="Matérn" value="Matern" />
                        <el-option label="Linear (线性)" value="Linear" />
                        <el-option label="Periodic (周期)" value="Periodic" />
                      </el-select>
                      <div class="help-text">选择协方差函数形式</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="优化器 optimizer">
                      <el-select v-model="params.gpr.optimizer" style="width: 100%">
                        <el-option label="L-BFGS-B" value="L-BFGS-B" />
                        <el-option label="Adam" value="Adam" />
                        <el-option label="Nelder-Mead" value="Nelder-Mead" />
                      </el-select>
                      <div class="help-text">用于最大化对数似然的优化算法</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="噪声 noise">
                  <el-slider v-model="params.gpr.noise" :min="1e-5" :max="0.1" :step="0.0001" :precision="5" show-input />
                  <div class="help-text">观测噪声方差 sigma_n^2 的初始值</div>
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="长度尺度 lengthScale">
                      <el-slider v-model="params.gpr.lengthScale" :min="0.1" :max="10" :step="0.1" :precision="2" show-input />
                      <div class="help-text">RBF / Matérn 核的长度尺度参数</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="信号方差 signalVariance">
                      <el-slider v-model="params.gpr.signalVariance" :min="0.01" :max="10" :step="0.01" :precision="3" show-input />
                      <div class="help-text">核函数信号幅度 sigma_f^2</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="最大迭代 maxIterOpt">
                  <el-slider v-model="params.gpr.maxIterOpt" :min="100" :max="5000" :step="50" show-input />
                  <div class="help-text">优化器迭代上限</div>
                </el-form-item>
              </el-form>
            </div>

            <!-- 3DVAR -->
            <div v-else-if="activeAlgo === 'three-d-var'">
              <el-form label-position="top" class="params-form">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="背景误差 B 缩放 (bFactor)">
                      <el-slider v-model="params.threeDVar.bFactor" :min="0.5" :max="2" :step="0.05" :precision="2" show-input />
                      <div class="help-text">背景误差协方差矩阵 B 的整体缩放系数</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="观测误差 R 缩放 (rFactor)">
                      <el-slider v-model="params.threeDVar.rFactor" :min="0.5" :max="2" :step="0.05" :precision="2" show-input />
                      <div class="help-text">观测误差协方差矩阵 R 的整体缩放系数</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="收敛阈值 convergence">
                  <el-slider
                    v-model="params.threeDVar.convergence"
                    :min="1e-6" :max="1e-2" :step="1e-6" :precision="6" show-input
                  />
                  <div class="help-text">增量范数低于该值即认为收敛</div>
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="最大迭代 maxIter">
                      <el-slider v-model="params.threeDVar.maxIter" :min="10" :max="200" :step="1" show-input />
                      <div class="help-text">3DVAR 代价函数最小化迭代上限</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="增量截断 incrementCutoff">
                      <el-slider v-model="params.threeDVar.incrementCutoff" :min="0" :max="1" :step="0.05" :precision="2" show-input />
                      <div class="help-text">分析增量低于该比例时被强制截断为 0</div>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>

            <!-- 4DVAR -->
            <div v-else-if="activeAlgo === 'four-d-var'">
              <el-form label-position="top" class="params-form">
                <el-form-item label="时间窗长度 windowLength (小时)">
                  <el-slider v-model="params.fourDVar.windowLength" :min="1" :max="12" :step="1" show-input />
                  <div class="help-text">四维变分的同化时间窗口</div>
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="外部迭代 outerIter">
                      <el-slider v-model="params.fourDVar.outerIter" :min="1" :max="10" :step="1" show-input />
                      <div class="help-text">非线性代价函数外层循环次数</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="内部迭代 innerIter">
                      <el-slider v-model="params.fourDVar.innerIter" :min="10" :max="100" :step="5" show-input />
                      <div class="help-text">每个外步内部线性求解迭代上限</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="TLM/Adjoint 步长 tlmStep">
                      <el-slider v-model="params.fourDVar.tlmStep" :min="0.01" :max="1" :step="0.01" :precision="2" show-input />
                      <div class="help-text">切线性 / 伴随模式的数值步长</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="正则化 regularization">
                      <el-slider v-model="params.fourDVar.regularization" :min="0" :max="0.1" :step="0.005" :precision="3" show-input />
                      <div class="help-text">代价函数 L2 正则项强度</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="背景误差因子 bgErrorFactor">
                  <el-slider v-model="params.fourDVar.bgErrorFactor" :min="0.5" :max="2" :step="0.05" :precision="2" show-input />
                  <div class="help-text">背景误差协方差矩阵的整体缩放系数</div>
                </el-form-item>
              </el-form>
            </div>

            <!-- 5DVAR -->
            <div v-else-if="activeAlgo === 'five-d-var'">
              <el-form label-position="top" class="params-form">
                <el-form-item label="时间窗长度 windowLength (小时)">
                  <el-slider v-model="params.fiveDVar.windowLength" :min="1" :max="24" :step="1" show-input />
                  <div class="help-text">四维变分的同化时间窗口</div>
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="外部迭代 outerIter">
                      <el-slider v-model="params.fiveDVar.outerIter" :min="1" :max="20" :step="1" show-input />
                      <div class="help-text">非线性代价函数外层循环次数</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="内部迭代 innerIter">
                      <el-slider v-model="params.fiveDVar.innerIter" :min="10" :max="200" :step="5" show-input />
                      <div class="help-text">每个外步内部线性求解迭代上限</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="TLM/Adjoint 步长 tlmStep">
                      <el-slider v-model="params.fiveDVar.tlmStep" :min="0.01" :max="1" :step="0.01" :precision="2" show-input />
                      <div class="help-text">切线性 / 伴随模式的数值步长</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="正则化 regularization">
                      <el-slider v-model="params.fiveDVar.regularization" :min="0" :max="1" :step="0.05" :precision="2" show-input />
                      <div class="help-text">代价函数 L2 正则项强度</div>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>

            <!-- EnKF -->
            <div v-else-if="activeAlgo === 'enkf'">
              <el-form label-position="top" class="params-form">
                <el-form-item label="集合成员数 ensembleSize">
                  <el-slider v-model="params.enkf.ensembleSize" :min="20" :max="500" :step="10" show-input />
                  <div class="help-text">Ensemble 大小，越大协方差估计越稳定但开销越高</div>
                </el-form-item>

                <el-form-item label="局地化半径 localizationRadius (km)">
                  <el-slider v-model="params.enkf.localizationRadius" :min="50" :max="2000" :step="10" show-input />
                  <div class="help-text">Schur product 局地化函数的影响半径</div>
                </el-form-item>

                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="膨胀因子 inflation">
                      <el-slider v-model="params.enkf.inflation" :min="0.9" :max="1.2" :step="0.01" :precision="3" show-input />
                      <div class="help-text">乘法协方差膨胀因子（1.0 表示不膨胀）</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="加法膨胀 covarianceInflation">
                      <el-slider v-model="params.enkf.covarianceInflation" :min="0" :max="0.5" :step="0.01" :precision="3" show-input />
                      <div class="help-text">加法协方差膨胀幅度</div>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="同化时间窗 assimilationWindow (小时)">
                  <el-slider v-model="params.enkf.assimilationWindow" :min="1" :max="12" :step="1" show-input />
                  <div class="help-text">两次同化分析之间的时间窗</div>
                </el-form-item>
              </el-form>
            </div>
          </div>

          <div class="bottom-actions">
            <el-button type="danger" plain @click="resetToDefaults">
              <el-icon><Refresh /></el-icon>&nbsp;重置为默认
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 右侧 · 实时评估面板 -->
      <div class="right-panel">
        <!-- 当前配置摘要 -->
        <el-card shadow="never" class="summary-card">
          <template #header>
            <div class="panel-title">
              <el-icon><DocumentCopy /></el-icon>&nbsp;当前配置摘要
              <span class="panel-sub">(可折叠 · 只读 JSON)</span>
            </div>
          </template>
          <el-collapse v-model="summaryCollapsed">
            <el-collapse-item :title="summaryTitle" name="1">
              <pre class="json-preview">{{ JSON.stringify(currentConfigJSON, null, 2) }}</pre>
            </el-collapse-item>
          </el-collapse>
        </el-card>

        <!-- 收敛曲线 -->
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="panel-title">
              <el-icon><TrendCharts /></el-icon>&nbsp;收敛曲线 · 代价函数值
              <span class="panel-sub">X = 迭代，Y = cost</span>
            </div>
          </template>
          <div ref="convergeChartRef" class="chart-box" style="height: 320px"></div>
        </el-card>

        <!-- 参数敏感性 -->
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="panel-title">
              <el-icon><PieChart /></el-icon>&nbsp;参数敏感性雷达图
              <span class="panel-sub">各主要参数对最终代价的贡献百分比（模拟）</span>
            </div>
          </template>
          <div ref="sensitivityChartRef" class="chart-box" style="height: 320px"></div>
        </el-card>

        <!-- 运行历史 -->
        <el-card shadow="never" class="history-card">
          <template #header>
            <div class="panel-title">
              <el-icon><Clock /></el-icon>&nbsp;运行历史
              <span class="panel-sub">最近 {{ history.length }} 条</span>
            </div>
          </template>
          <el-table :data="history" size="default" stripe style="width: 100%">
            <el-table-column prop="algoLabel" label="算法" min-width="130" />
            <el-table-column prop="time" label="运行时间" min-width="160" />
            <el-table-column prop="finalCost" label="收敛值" min-width="110">
              <template #default="scope">{{ Number(scope.row.finalCost).toFixed(6) }}</template>
            </el-table-column>
            <el-table-column label="状态" min-width="100">
              <template #default="scope">
                <el-tag :type="statusTagType(scope.row.status)" size="small" effect="light">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="耗时" min-width="90">
              <template #default="scope">{{ scope.row.durationMs }} ms</template>
            </el-table-column>
            <el-table-column label="操作" min-width="150" fixed="right">
              <template #default="scope">
                <el-button link type="primary" size="small" @click="viewDetail(scope.row)">查看详情</el-button>
                <el-popconfirm title="确定删除此记录？" @confirm="removeHistory(scope.row.id)">
                  <template #reference>
                    <el-button link type="danger" size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!history.length" class="empty-hint">暂无运行记录，点击右上角「开始调参 / 运行」生成一条。</div>
        </el-card>
      </div>
    </div>

    <!-- 保存模板弹窗 -->
    <el-dialog v-model="saveDialogVisible" title="保存为模板" width="460px">
      <el-form label-position="top">
        <el-form-item label="模板名称">
          <el-input v-model="newTemplateName" placeholder="例如：DE-RRT* 保守配置" maxlength="40" show-word-limit />
        </el-form-item>
        <el-form-item label="说明（可选）">
          <el-input v-model="newTemplateNote" type="textarea" :rows="3" placeholder="简要描述此参数的用途" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveTemplate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 加载模板弹窗 -->
    <el-dialog v-model="loadDialogVisible" title="加载已有模板" width="560px">
      <el-alert v-if="!templates.length" type="info" :closable="false" show-icon>
        暂无模板，调参后可通过「保存为模板」存储。
      </el-alert>
      <el-table v-else :data="templates" size="default" style="margin-top: 10px">
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="algoLabel" label="算法" min-width="130" />
        <el-table-column prop="savedAt" label="保存时间" min-width="160" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button link type="primary" size="small" @click="applyTemplate(scope.row)">载入</el-button>
            <el-popconfirm title="确定删除此模板？" @confirm="removeTemplate(scope.row.id)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  MagicStick, RefreshLeft, CollectionTag, VideoPlay, Download,
  Tools, DocumentCopy, TrendCharts, PieChart, Clock, FolderOpened, Refresh, Cpu
} from '@element-plus/icons-vue'

// ===== 常量定义 =====
const TEMPLATES_KEY = 'uav_param_templates_v1'
const HISTORY_KEY = 'uav_param_history_v1'

const algoMeta = {
  'vrptw':       { label: 'VRPTW',     tagType: 'primary' },
  'de-rrt-star': { label: 'DE-RRT*',   tagType: 'primary' },
  'dwa':         { label: 'DWA',       tagType: 'success' },
  'convlstm':    { label: 'ConvLSTM',  tagType: 'warning' },
  'xgboost':     { label: 'XGBoost',   tagType: 'warning' },
  'gpr':         { label: 'GPR',       tagType: 'warning' },
  'cnn':         { label: 'CNN',       tagType: 'warning' },
  'unet':        { label: 'U-Net',     tagType: 'warning' },
  'three-d-var': { label: '3DVAR',     tagType: 'info' },
  'four-d-var':  { label: '4DVAR',     tagType: 'info' },
  'five-d-var':  { label: '5DVAR',     tagType: 'info' },
  'enkf':        { label: 'EnKF',      tagType: 'danger' }
}

// 默认值
const DEFAULT_COMMON = {
  maxIterations: 1000,
  timeLimitSec: 60,
  randomSeed: 42
}

const DEFAULT_PARAMS = {
  vrptw:     { vehicleCount: 10, capacity: 100, timeWindowHard: true, penaltyDelay: 100, penaltyEarly: 10, maxRoutes: 50 },
  deRrtStar: { popSize: 150, maxIter: 2000, stepSize: 1.0, goalRadius: 2.0, elitism: 0.2, mutationRate: 0.08 },
  dwa:       { vMin: 0, vMax: 5, omegaMin: -1.57, omegaMax: 1.57, dtPred: 0.1, alphaGain: 1.5, betaGain: 3.0, gammaGain: 1.0, samples: 30 },
  convlstm:  { hiddenDim: 64, numLayers: 3, seqLen: 24, dropout: 0.2, learningRate: 0.001, batchSize: 32, epochs: 50 },
  xgboost:   { maxDepth: 6, learningRate: 0.1, nEstimators: 100, subsample: 0.8, colsampleByTree: 0.8, regAlpha: 0.1, regLambda: 1.0 },
  gpr:       { kernel: 'RBF', optimizer: 'L-BFGS-B', noise: 0.01, lengthScale: 1.0, signalVariance: 1.0, maxIterOpt: 1000 },
  cnn:       { filters: 64, kernelSize: 3, strides: 1, padding: 'same', activation: 'relu', dropout: 0.3, learningRate: 0.001, epochs: 30 },
  unet:      { baseFilters: 64, depth: 4, activation: 'relu', dropout: 0.2, learningRate: 0.0001, epochs: 50, loss: 'mse' },
  threeDVar: { bFactor: 1.0, rFactor: 1.0, convergence: 1e-4, maxIter: 50, incrementCutoff: 0.01 },
  fourDVar:  { windowLength: 6, outerIter: 3, innerIter: 30, tlmStep: 0.1, regularization: 0.01, bgErrorFactor: 1.0 },
  fiveDVar:  { windowLength: 6, outerIter: 5, innerIter: 50, tlmStep: 0.1, regularization: 0.05 },
  enkf:      { ensembleSize: 80, localizationRadius: 500, inflation: 1.02, covarianceInflation: 0.02, assimilationWindow: 3 }
}

// 参数键名映射（供 JSON 输出使用）
const ALGO_PARAM_KEYS = {
  'vrptw':       'vrptw',
  'de-rrt-star': 'deRrtStar',
  'dwa':         'dwa',
  'convlstm':    'convlstm',
  'xgboost':     'xgboost',
  'gpr':         'gpr',
  'cnn':         'cnn',
  'unet':        'unet',
  'three-d-var': 'threeDVar',
  'four-d-var':  'fourDVar',
  'five-d-var':  'fiveDVar',
  'enkf':        'enkf'
}

// 雷达图指标：每个算法取 5 个主要参数
const SENSITIVITY_KEYS = {
  'vrptw':       ['vehicleCount', 'capacity', 'penaltyDelay', 'penaltyEarly', 'maxRoutes'],
  'de-rrt-star': ['popSize', 'maxIter', 'stepSize', 'goalRadius', 'elitism'],
  'dwa':         ['alphaGain', 'betaGain', 'gammaGain', 'dtPred', 'samples'],
  'convlstm':    ['hiddenDim', 'numLayers', 'seqLen', 'dropout', 'learningRate'],
  'xgboost':     ['maxDepth', 'learningRate', 'nEstimators', 'subsample', 'colsampleByTree'],
  'gpr':         ['lengthScale', 'signalVariance', 'noise', 'maxIterOpt', 'kernel'],
  'cnn':         ['filters', 'kernelSize', 'dropout', 'learningRate', 'epochs'],
  'unet':        ['baseFilters', 'depth', 'dropout', 'learningRate', 'epochs'],
  'three-d-var': ['bFactor', 'rFactor', 'convergence', 'maxIter', 'incrementCutoff'],
  'four-d-var':  ['windowLength', 'outerIter', 'innerIter', 'tlmStep', 'regularization'],
  'five-d-var':  ['windowLength', 'outerIter', 'innerIter', 'tlmStep', 'regularization'],
  'enkf':        ['ensembleSize', 'localizationRadius', 'inflation', 'covarianceInflation', 'assimilationWindow']
}

// ===== 响应式状态 =====
const activeAlgo = ref('de-rrt-star')
const commonParams = reactive({ ...DEFAULT_COMMON })
const params = reactive(JSON.parse(JSON.stringify(DEFAULT_PARAMS)))
const running = ref(false)
const history = ref([])
const templates = ref([])
const summaryCollapsed = ref(['1'])

const saveDialogVisible = ref(false)
const newTemplateName = ref('')
const newTemplateNote = ref('')
const loadDialogVisible = ref(false)

// ECharts
const convergeChartRef = ref(null)
const sensitivityChartRef = ref(null)
let convergeChart = null
let sensitivityChart = null

// ===== 计算属性 =====
const currentConfigJSON = computed(() => ({
  algorithm: activeAlgo.value,
  algorithmLabel: algoMeta[activeAlgo.value].label,
  common: { ...commonParams },
  [ALGO_PARAM_KEYS[activeAlgo.value]]: { ...params[ALGO_PARAM_KEYS[activeAlgo.value]] }
}))

const summaryTitle = computed(() => {
  const algo = algoMeta[activeAlgo.value].label
  return `${algo} · 共 ${Object.keys(currentConfigJSON.value).length - 1} 个分组 · 点击展开查看 JSON`
})

// ===== 工具函数 =====
function pad(n) { return n < 10 ? '0' + n : '' + n }
function fmtDateTime(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function statusTagType(status) {
  if (status === '成功') return 'success'
  if (status === '失败') return 'danger'
  return 'info'
}

function seededRand(seed) {
  let s = seed || 1
  return function () {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

// ===== 参数默认 / 重置 =====
function loadDefaults() {
  Object.assign(commonParams, DEFAULT_COMMON)
  Object.keys(DEFAULT_PARAMS).forEach(k => {
    Object.assign(params[k], DEFAULT_PARAMS[k])
  })
  ElMessage.success('已加载全部默认参数')
}

function resetToDefaults() {
  Object.assign(commonParams, DEFAULT_COMMON)
  const key = ALGO_PARAM_KEYS[activeAlgo.value]
  Object.assign(params[key], DEFAULT_PARAMS[key])
  ElMessage.success(`已重置 ${algoMeta[activeAlgo.value].label} 为默认值`)
}

// ===== 模拟调优 =====
function generateConvergenceData(seed) {
  const rand = seededRand(seed || 7)
  const iterations = Math.min(commonParams.maxIterations, 200)
  const startCost = 10 + rand() * 20
  const floor = 0.5 + rand() * 1.5
  const decay = 0.96 + rand() * 0.02
  const data = []
  let prev = startCost
  for (let i = 0; i < iterations; i++) {
    const target = floor + (startCost - floor) * Math.pow(decay, i)
    const noise = (rand() - 0.5) * 0.1 * Math.max(0.1, target - floor)
    prev = Math.max(floor * 0.9, target + noise)
    data.push(Number(prev.toFixed(6)))
  }
  return data
}

function generateSensitivity(seed) {
  const rand = seededRand(seed || 11)
  const keys = SENSITIVITY_KEYS[activeAlgo.value]
  const raw = keys.map(() => 10 + rand() * 90)
  const sum = raw.reduce((a, b) => a + b, 0)
  return raw.map(v => Number(((v / sum) * 100).toFixed(2)))
}

function startTuning() {
  if (running.value) return
  running.value = true
  const startedAt = Date.now()
  const seed = commonParams.randomSeed || startedAt
  const data = generateConvergenceData(seed)
  const sensitivity = generateSensitivity(seed)

  setTimeout(() => {
    const duration = Date.now() - startedAt
    const finalCost = data[data.length - 1]
    const record = {
      id: startedAt,
      algo: activeAlgo.value,
      algoLabel: algoMeta[activeAlgo.value].label,
      time: fmtDateTime(new Date(startedAt)),
      finalCost,
      status: finalCost > 0 ? '成功' : '失败',
      durationMs: duration,
      paramsSnapshot: JSON.parse(JSON.stringify(currentConfigJSON.value))
    }
    history.value.unshift(record)
    if (history.value.length > 10) history.value.length = 10
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value)) } catch (e) {}

    nextTick(() => renderCharts(data, sensitivity))
    ElMessage.success(`${algoMeta[activeAlgo.value].label} 调优完成 · 最终代价 ${finalCost.toFixed(4)}`)
    running.value = false
  }, 1200)
}

// ===== 历史操作 =====
function viewDetail(row) {
  const text = `算法：${row.algoLabel}\n时间：${row.time}\n收敛值：${row.finalCost}\n耗时：${row.durationMs} ms\n\n参数快照：\n${JSON.stringify(row.paramsSnapshot, null, 2)}`
  ElMessage({ message: `已记录 ${row.algoLabel} 的调优详情`, type: 'info', duration: 2500 })
  // 简单展示：复制到剪贴板以便查看
  try {
    navigator.clipboard && navigator.clipboard.writeText(text)
  } catch (e) {}
}

function removeHistory(id) {
  history.value = history.value.filter(r => r.id !== id)
  try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value)) } catch (e) {}
  ElMessage.success('已删除记录')
}

// ===== 模板管理 =====
function openSaveTemplate() {
  newTemplateName.value = `${algoMeta[activeAlgo.value].label}-${fmtDateTime(new Date())}`
  newTemplateNote.value = ''
  saveDialogVisible.value = true
}

function confirmSaveTemplate() {
  if (!newTemplateName.value.trim()) {
    ElMessage.warning('请填写模板名称')
    return
  }
  const tpl = {
    id: Date.now(),
    name: newTemplateName.value.trim(),
    note: newTemplateNote.value.trim(),
    algo: activeAlgo.value,
    algoLabel: algoMeta[activeAlgo.value].label,
    params: JSON.parse(JSON.stringify({ common: { ...commonParams }, ...params })),
    savedAt: fmtDateTime(new Date())
  }
  templates.value.unshift(tpl)
  try { localStorage.setItem(TEMPLATES_KEY, JSON.stringify(templates.value)) } catch (e) {}
  saveDialogVisible.value = false
  ElMessage.success(`模板「${tpl.name}」已保存`)
}

function loadTemplates() {
  loadDialogVisible.value = true
}

function applyTemplate(tpl) {
  if (tpl.algo) activeAlgo.value = tpl.algo
  if (tpl.params?.common) Object.assign(commonParams, tpl.params.common)
  Object.keys(DEFAULT_PARAMS).forEach(k => {
    if (tpl.params && tpl.params[k]) Object.assign(params[k], tpl.params[k])
  })
  loadDialogVisible.value = false
  ElMessage.success(`已载入模板「${tpl.name}」`)
}

function removeTemplate(id) {
  templates.value = templates.value.filter(t => t.id !== id)
  try { localStorage.setItem(TEMPLATES_KEY, JSON.stringify(templates.value)) } catch (e) {}
  ElMessage.success('模板已删除')
}

// ===== 导出 JSON =====
function exportJSON() {
  const payload = {
    ...currentConfigJSON.value,
    exportedAt: new Date().toISOString(),
    version: 'v1'
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const ts = new Date()
  const stamp = `${ts.getFullYear()}${pad(ts.getMonth() + 1)}${pad(ts.getDate())}_${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}`
  a.download = `params_${activeAlgo.value}_${stamp}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('JSON 配置已导出')
}

// ===== 图表渲染 =====
function renderCharts(convergeData, sensitivityData) {
  renderConverge(convergeData)
  renderSensitivity(sensitivityData)
}

function renderConverge(data) {
  if (!convergeChartRef.value) return
  if (!convergeChart) convergeChart = echarts.init(convergeChartRef.value)
  const xData = data ? data.map((_, i) => i + 1) : []
  const series = data ? data : []
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      name: '迭代',
      data: xData,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '代价函数',
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    dataZoom: [{ type: 'inside' }],
    series: [{
      name: '代价',
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: '#409EFF' },
      areaStyle: { color: 'rgba(64,158,255,0.12)' },
      data: series
    }]
  }
  convergeChart.setOption(option, true)
}

function renderSensitivity(data) {
  if (!sensitivityChartRef.value) return
  if (!sensitivityChart) sensitivityChart = echarts.init(sensitivityChartRef.value)
  const keys = SENSITIVITY_KEYS[activeAlgo.value]
  const indicator = keys.map(k => ({ name: k, max: 100 }))
  const values = data || keys.map(() => 20)
  const option = {
    tooltip: {},
    radar: {
      indicator,
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#333' }
    },
    series: [{
      name: '参数敏感性',
      type: 'radar',
      data: [{
        value: values,
        name: `${algoMeta[activeAlgo.value].label} 敏感性`,
        areaStyle: { color: 'rgba(82,196,26,0.25)' },
        lineStyle: { color: '#52c41a', width: 2 },
        itemStyle: { color: '#52c41a' }
      }]
    }]
  }
  sensitivityChart.setOption(option, true)
}

function onResize() {
  convergeChart && convergeChart.resize()
  sensitivityChart && sensitivityChart.resize()
}

// ===== 生命周期 =====
onMounted(() => {
  // 读取模板与历史（localStorage）
  try {
    const tplRaw = localStorage.getItem(TEMPLATES_KEY)
    if (tplRaw) templates.value = JSON.parse(tplRaw)
    const histRaw = localStorage.getItem(HISTORY_KEY)
    if (histRaw) history.value = JSON.parse(histRaw).slice(0, 10)
  } catch (e) {}

  nextTick(() => {
    renderCharts(null, null)
  })
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  convergeChart && convergeChart.dispose()
  sensitivityChart && sensitivityChart.dispose()
  convergeChart = null
  sensitivityChart = null
})

// 切换算法时重绘雷达图（保留空白收敛曲线，等待下一次调参）
watch(activeAlgo, () => {
  nextTick(() => renderSensitivity(null))
})
</script>

<style scoped>
.parameter-tuning {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 顶部栏 */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  background: #fff;
  border-radius: 10px;
  padding: 14px 20px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.top-bar-left { display: flex; align-items: center; gap: 12px; }
.page-title { margin: 0; font-size: 18px; font-weight: 600; color: #24292f; }
.top-bar-controls { display: flex; gap: 8px; flex-wrap: wrap; }
.demo-tag { font-size: 12px; }

/* 算法选择器 */
.algo-select-container {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  border-radius: 10px;
  padding: 16px 20px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.algo-select-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #24292f;
}
.algo-select {
  width: 400px;
}
@media (max-width: 768px) {
  .algo-select-container {
    flex-direction: column;
    align-items: flex-start;
  }
  .algo-select {
    width: 100%;
  }
}

/* 主体 */
.main-body {
  display: grid;
  grid-template-columns: 35% 1fr;
  gap: 16px;
}
@media (max-width: 1200px) {
  .main-body { grid-template-columns: 1fr; }
}

/* 左侧参数卡 */
.params-card { border-radius: 10px; }
.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #24292f;
}
.panel-sub {
  font-size: 12px;
  font-weight: 400;
  color: #8a8f98;
  margin-left: 4px;
}
.section-block { margin-top: 6px; }
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #57606a;
  margin: 8px 0 12px;
  padding-left: 8px;
  border-left: 3px solid #409EFF;
}
.params-form :deep(.el-form-item) { margin-bottom: 14px; }
.help-text { font-size: 12px; color: #8a8f98; line-height: 1.5; margin-top: 4px; }
.bottom-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #eaecef;
}

/* 右侧面板 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.summary-card, .chart-card, .history-card { border-radius: 10px; }
.json-preview {
  background: #f6f8fa;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
  max-height: 240px;
  overflow: auto;
  margin: 0;
  color: #24292f;
}
.chart-box { width: 100%; }
.empty-hint {
  text-align: center;
  color: #8a8f98;
  font-size: 12px;
  padding: 16px 0 4px;
}
</style>
