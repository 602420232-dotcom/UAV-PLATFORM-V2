/**
 * 4D轨迹可视化 - Cesium时间轴播放
 * 三维轨迹(x,y,z) + 时间维度(t) 完整可视化
 */
import * as Cesium from 'cesium';

export class Trajectory4DVisualizer {
  constructor(viewer) {
    this.viewer = viewer;
    this.timelineEntities = [];
    this.clock = viewer.clock;
    this.timeline = viewer.timeline;
    this.isPlaying = false;
    this.currentPath = null;
  }

  render4DTrajectory(trackData, droneId = 'UAV-001', color = Cesium.Color.ORANGE) {
    const positions = trackData.track.map(p =>
      Cesium.Cartesian3.fromDegrees(p.x, p.y, p.z)
    );
    const times = trackData.track.map(p => Cesium.JulianDate.fromIso8601(p.t));

    // 时间动态路径
    const timeDynamicPosition = new Cesium.TimeIntervalCollection();
    positions.forEach((pos, i) => {
      timeDynamicPosition.addInterval(
        Cesium.TimeInterval.fromIso8601({
          iso8601: trackData.track[i].t,
          data: { position: pos }
        })
      );
    });

    // 主轨迹线
    const trajectoryEntity = this.viewer.entities.add({
      id: `trajectory_4d_${droneId}`,
      polyline: {
        positions: new Cesium.CallbackProperty(() => {
          if (!this.currentPath) return positions;
          return this.currentPath.map(p =>
            Cesium.Cartesian3.fromDegrees(p.x, p.y, p.z)
          );
        }, false),
        width: 4,
        material: new Cesium.PolylineGlowMaterialProperty({
          glowPower: 0.2,
          color: color
        })
      },
      // 起点标记
      billboard: {
        image: '/markers/start.png',
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM
      },
      // 终点标记
      label: {
        text: droneId,
        font: '14px monospace',
        fillColor: Cesium.Color.WHITE,
        pixelOffset: new Cesium.Cartesian2(0, -20)
      }
    });
    this.timelineEntities.push(trajectoryEntity);

    // 动态无人机模型
    const droneEntity = this.viewer.entities.add({
      id: `drone_4d_${droneId}`,
      position: new Cesium.SampledPositionProperty(),
      point: { pixelSize: 10, color: color, outlineColor: Cesium.Color.WHITE, outlineWidth: 2 },
      path: {
        resolution: 1,
        material: color.withAlpha(0.3),
        width: 2,
        leadTime: 0,
        trailTime: 60
      }
    });

    const positionProperty = droneEntity.position;
    trackData.track.forEach((p, i) => {
      const time = Cesium.JulianDate.fromIso8601(p.t);
      const pos = Cesium.Cartesian3.fromDegrees(p.x, p.y, p.z);
      positionProperty.addSample(time, pos);
    });

    // 时间轴设置
    const start = Cesium.JulianDate.fromIso8601(trackData.metadata.start_time);
    const stop = Cesium.JulianDate.fromIso8601(trackData.metadata.end_time);
    this.clock.startTime = start.clone();
    this.clock.stopTime = stop.clone();
    this.clock.currentTime = start.clone();
    this.clock.multiplier = 10;
    this.clock.shouldAnimate = true;

    this.timeline.zoomTo(start, stop);
    this.viewer.zoomTo(droneEntity, new Cesium.HeadingPitchRange(0, -30, 5000));

    return { trajectoryEntity, droneEntity };
  }

  // 速度/高度剖面图
  showSpeedProfile(trackData) {
    const speeds = trackData.track.map(p => ({
      time: p.t, speed: p.speed || 0, altitude: p.z
    }));
    return speeds;
  }

  // 添加风场4D可视化
  render4DWindField(windData, timeRange) {
    windData.forEach(w => {
      const entity = this.viewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(w.lon, w.lat, w.alt || 100),
        polyline: {
          positions: Cesium.Cartesian3.fromDegreesArray([
            w.lon, w.lat,
            w.lon + w.u * 0.01, w.lat + w.v * 0.01
          ]),
          width: 2,
          material: Cesium.Color.fromCssColorString('#00d4ff').withAlpha(0.4),
          clampToGround: true
        },
        availability: new Cesium.TimeIntervalCollection([
          new Cesium.TimeInterval({
            start: Cesium.JulianDate.fromIso8601(timeRange.start),
            stop: Cesium.JulianDate.fromIso8601(timeRange.end)
          })
        ])
      });
      this.timelineEntities.push(entity);
    });
  }

  play() { this.clock.shouldAnimate = true; this.isPlaying = true; }
  pause() { this.clock.shouldAnimate = false; this.isPlaying = false; }

  setSpeed(multiplier) {
    this.clock.multiplier = multiplier;
  }

  destroy() {
    this.timelineEntities.forEach(e => this.viewer.entities.remove(e));
    this.timelineEntities = [];
  }
}
