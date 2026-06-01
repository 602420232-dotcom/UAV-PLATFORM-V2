/**
 * 可视化增强 - 3D轨迹 + 气象场动态展示 + 多无人机协同
 * 基于Cesium + ECharts
 */
import * as Cesium from 'cesium';
import * as echarts from 'echarts';

export class EnhancedVisualizer {
  constructor(containerId, options = {}) {
    this.viewer = new Cesium.Viewer(containerId, {
      terrain: Cesium.Terrain.fromWorldTerrain(),
      animation: false,
      timeline: true,
      ...options
    });
    this.trajectoryLayers = new Map();
    this.droneEntities = new Map();
    this.weatherLayers = [];
    this.conflictWarnings = [];
  }

  render3DTrajectory(droneId, waypoints, color = Cesium.Color.ORANGE) {
    if (this.trajectoryLayers.has(droneId)) {
      this.viewer.entities.remove(this.trajectoryLayers.get(droneId));
    }
    const positions = waypoints.map(([lng, lat, alt = 100]) =>
      Cesium.Cartesian3.fromDegrees(lng, lat, alt)
    );
    const entity = this.viewer.entities.add({
      id: `trajectory_${droneId}`,
      polyline: {
        positions: positions,
        width: 3,
        material: color.withAlpha(0.8),
        clampToGround: false,
        zIndex: 10
      },
      polylineGlow: { glowPower: 0.2, color: color }
    });
    this.trajectoryLayers.set(droneId, entity);
  }

  renderMultiDrone(drones) {
    drones.forEach((drone, index) => {
      if (this.droneEntities.has(drone.id)) {
        const entity = this.droneEntities.get(drone.id);
        entity.position.setValue(Cesium.Cartesian3.fromDegrees(
          drone.position.lon, drone.position.lat, drone.position.alt || 100
        ));
      } else {
        const colors = [Cesium.Color.ORANGE, Cesium.Color.CYAN, Cesium.Color.LIME, Cesium.Color.MAGENTA];
        const entity = this.viewer.entities.add({
          id: `drone_${drone.id}`,
          position: Cesium.Cartesian3.fromDegrees(
            drone.position.lon, drone.position.lat, drone.position.alt || 100
          ),
          point: { pixelSize: 12, color: colors[index % colors.length], outlineColor: Cesium.Color.WHITE, outlineWidth: 2 },
          label: {
            text: drone.id,
            font: '12px monospace',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            pixelOffset: new Cesium.Cartesian2(0, -20)
          },
          ellipsoid: {
            radii: new Cesium.Cartesian3(500, 500, 200),
            material: Cesium.Color.fromCssColorString('#00d4ff').withAlpha(0.05),
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString('#00d4ff').withAlpha(0.2)
          }
        });
        this.droneEntities.set(drone.id, entity);
      }
    });
  }

  renderWeatherField(windArrows) {
    this.weatherLayers.forEach(l => this.viewer.entities.remove(l));
    this.weatherLayers = [];
    windArrows.forEach(w => {
      const length = w.speed * 1000;
      const angle = Math.atan2(w.v, w.u);
      const endLat = w.lat + (length * Math.cos(angle)) / 111000;
      const endLon = w.lon + (length * Math.sin(angle)) / (111000 * Math.cos(w.lat * Math.PI / 180));
      const entity = this.viewer.entities.add({
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray([w.lon, w.lat, endLon, endLat]),
          width: 2,
          material: Cesium.Color.fromCssColorString(w.color).withAlpha(0.6),
          arrows: Cesium.ArrowStyle.END,
          clampToGround: true
        }
      });
      this.weatherLayers.push(entity);
    });
  }

  showConflictWarning(conflicts) {
    this.conflictWarnings.forEach(e => this.viewer.entities.remove(e));
    this.conflictWarnings = [];
    conflicts.forEach(c => {
      const entity = this.viewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(c.lon, c.lat, 100),
        label: {
          text: `⚠ 冲突: ${c.distance_m.toFixed(0)}m`,
          font: '14px sans-serif',
          fillColor: Cesium.Color.RED,
          scale: 1.5,
          pixelOffset: new Cesium.Cartesian2(0, -30)
        },
        point: { pixelSize: 20, color: Cesium.Color.RED.withAlpha(0.5) }
      });
      this.conflictWarnings.push(entity);
    });
  }

  flyToExtent(bounds) {
    const rect = Cesium.Rectangle.fromDegrees(bounds.west, bounds.south, bounds.east, bounds.north);
    this.viewer.camera.flyTo({ destination: rect });
  }

  destroy() {
    this.viewer.destroy();
  }
}

export class MultiDroneECharts {
  constructor(containerId) {
    this.chart = echarts.init(document.getElementById(containerId));
  }

  updateDronePositions(drones) {
    this.chart.setOption({
      title: { text: '多无人机协同态势', left: 'center' },
      tooltip: { trigger: 'item' },
      xAxis: { type: 'value', name: '经度' },
      yAxis: { type: 'value', name: '纬度' },
      series: [{
        type: 'scatter',
        symbolSize: (val, params) => Math.max(10, params.data[2] / 5),
        data: drones.map(d => [d.position.lon, d.position.lat, d.battery || 100]),
        itemStyle: {
          color: params => {
            const battery = params.data[2];
            return battery > 60 ? '#00ff88' : battery > 30 ? '#ffd700' : '#ff4444';
          }
        },
        label: {
          show: true,
          formatter: params => params.name,
          position: 'right'
        }
      }]
    });
  }
}
