/**
 * 增强现实数字地图
 * 3D路径可视化 + 气象热力图叠加 + 实时无人机位置追踪
 */
import * as Cesium from 'cesium';
import * as echarts from 'echarts';

export class ARDigitalMap {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.viewer = null;
    this.entities = [];
    this.heatmapLayer = null;
    this.flightPath = [];
    this.init();
  }

  init() {
    Cesium.Ion.defaultAccessToken = 'your-cesium-token';
    this.viewer = new Cesium.Viewer(this.container, {
      terrain: Cesium.Terrain.fromWorldTerrain(),
      animation: false,
      timeline: false,
      baseLayerPicker: false
    });
    this.viewer.scene.globe.enableLighting = true;
  }

  render3DPath(waypoints, color = Cesium.Color.ORANGE) {
    const positions = waypoints.map(([x, y, z = 100]) =>
      Cesium.Cartesian3.fromDegrees(x, y, z)
    );
    const pathEntity = this.viewer.entities.add({
      polyline: {
        positions: positions,
        width: 4,
        material: color,
        clampToGround: false,
        zIndex: 10
      }
    });
    this.entities.push(pathEntity);
    return pathEntity;
  }

  renderWeatherHeatmap(weatherGrid, bounds) {
    const { west, south, east, north } = bounds;
    const layer = this.viewer.scene.primitives.add(
      new Cesium.GroundPrimitive({
        geometryInstances: weatherGrid.map((cell) => {
          const color = this.riskToColor(cell.riskLevel);
          return new Cesium.GeometryInstance({
            geometry: new Cesium.RectangleGeometry({
              rectangle: Cesium.Rectangle.fromDegrees(
                cell.lon, cell.lat, cell.lon + 0.5, cell.lat + 0.5
              )
            }),
            attributes: {
              color: Cesium.ColorGeometryInstanceAttribute.fromColor(color)
            }
          });
        })
      })
    );
    this.heatmapLayer = layer;
  }

  riskToColor(risk) {
    if (risk === 'HIGH') return Cesium.Color.RED.withAlpha(0.5);
    if (risk === 'MEDIUM') return Cesium.Color.YELLOW.withAlpha(0.4);
    return Cesium.Color.GREEN.withAlpha(0.3);
  }

  trackDrone(droneId, getPositionFn) {
    const droneEntity = this.viewer.entities.add({
      id: droneId,
      position: new Cesium.CallbackProperty(() => {
        const pos = getPositionFn();
        return Cesium.Cartesian3.fromDegrees(pos.lon, pos.lat, pos.alt || 100);
      }, false),
      model: {
        uri: '/models/uav.glb',
        scale: 1.0,
        silhouetteColor: Cesium.Color.WHITE
      },
      label: {
        text: droneId,
        font: '14px sans-serif',
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        pixelOffset: new Cesium.Cartesian2(0, -30)
      }
    });
    this.entities.push(droneEntity);
    return droneEntity;
  }

  showObstacleWarning(obstacles) {
    obstacles.forEach(obs => {
      this.viewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(obs.lon, obs.lat, 0),
        ellipse: {
          semiMinorAxis: obs.radius * 1000,
          semiMajorAxis: obs.radius * 1000,
          material: Cesium.Color.RED.withAlpha(0.3),
          outline: true,
          outlineColor: Cesium.Color.RED
        },
        label: {
          text: '⚠ 障碍物',
          font: '12px sans-serif',
          fillColor: Cesium.Color.RED
        }
      });
    });
  }

  async fetchWeatherOverlay(bounds) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);
    try {
      const response = await fetch('/api/weather/heatmap', {
        method: 'POST',
        body: JSON.stringify(bounds),
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      this.renderWeatherHeatmap(data.grid, bounds);
      return data;
    } catch (error) {
      console.error('天气数据获取失败:', error.message);
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  flyTo(lon, lat, alt = 500000) {
    this.viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(lon, lat, alt)
    });
  }

  destroy() {
    this.entities.forEach(e => this.viewer.entities.remove(e));
    if (this.heatmapLayer) {
      this.viewer.scene.primitives.remove(this.heatmapLayer);
    }
  }
}
