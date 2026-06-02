import * as THREE from 'three';

const PERF = {
    mobile: window.innerWidth < 768,
    lowPerf: window.innerWidth < 480,
    dpr: Math.min(window.devicePixelRatio, 2),
};

class SectionScene {
    constructor(sectionEl, opts = {}) {
        this.el = sectionEl;
        this.opts = opts;

        this.container = document.createElement('div');
        this.container.className = 'three-bg';
        this.container.style.cssText = 'position:absolute;inset:0;z-index:0;pointer-events:none;overflow:hidden;';
        this.el.style.position = 'relative';
        this.el.prepend(this.container);

        const { w, h } = this.size();
        this.camera = new THREE.PerspectiveCamera(opts.fov || 60, w / h, 0.1, 100);
        this.camera.position.set(0, opts.camY || 0, opts.camZ || 5);
        this.camera.lookAt(0, 0, 0);

        this.scene = new THREE.Scene();
        this.renderer = new THREE.WebGLRenderer({
            alpha: true,
            antialias: !PERF.lowPerf,
            powerPreference: 'low-power',
        });
        this.renderer.setPixelRatio(PERF.dpr);
        this.renderer.setSize(w, h);
        this.renderer.setClearColor(0x000000, 0);
        this.container.appendChild(this.renderer.domElement);

        this.clock = new THREE.Clock();
        this.running = true;
        this.scrollProgress = 0;

        this.init();
        this.animate();
    }

    size() {
        return { w: this.el.clientWidth, h: this.el.clientHeight };
    }

    init() {}
    update(dt) {}

    animate() {
        if (!this.running) return;
        requestAnimationFrame(() => this.animate());
        this.update(this.clock.getDelta());
        this.renderer.render(this.scene, this.camera);
    }

    onScroll(progress) {
        this.scrollProgress = progress;
    }

    resize() {
        const { w, h } = this.size();
        if (w === 0 || h === 0) return;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    }

    dispose() {
        this.running = false;
        this.scene.traverse(obj => {
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) {
                if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
                else obj.material.dispose();
            }
        });
        this.renderer.dispose();
        this.container.remove();
    }
}

class HeroScene extends SectionScene {
    init() {
        this.scene.fog = new THREE.FogExp2(0x0d2418, 0.014);

        const ambient = new THREE.AmbientLight(0x336644, 0.5);
        this.scene.add(ambient);
        const dir = new THREE.DirectionalLight(0x99ddbb, 1.2);
        dir.position.set(5, 10, 5);
        this.scene.add(dir);
        const fill = new THREE.DirectionalLight(0x557766, 0.4);
        fill.position.set(-3, 2, -3);
        this.scene.add(fill);

        this.terrainLayers = [];
        const layers = [
            { w: 30, d: 18, segs: 64, amp: 0.5, freq: 0.5, color: 0x0d2a1a, op: 0.35, y: 0 },
            { w: 22, d: 14, segs: 48, amp: 0.35, freq: 0.7, color: 0x123522, op: 0.50, y: 0.15 },
            { w: 16, d: 10, segs: 32, amp: 0.25, freq: 0.9, color: 0x19472b, op: 0.65, y: 0.3 },
            { w: 10, d: 6, segs: 24, amp: 0.15, freq: 1.2, color: 0x2a5e3a, op: 0.80, y: 0.5 },
        ];

        if (PERF.mobile) layers.forEach(l => { l.segs = Math.floor(l.segs / 2); });

        layers.forEach(cfg => {
            const geo = new THREE.PlaneGeometry(cfg.w, cfg.d, cfg.segs, cfg.segs);
            geo.rotateX(-Math.PI / 2);
            const pos = geo.attributes.position;
            for (let i = 0; i < pos.count; i++) {
                const x = pos.getX(i);
                const z = pos.getZ(i);
                const y = cfg.amp * (
                    Math.sin(x * cfg.freq + z * cfg.freq * 0.6) * 0.5 +
                    Math.sin(x * cfg.freq * 2.1 + 1.3) * 0.3 +
                    Math.sin(z * cfg.freq * 1.7 + 0.7) * 0.2
                );
                pos.setY(i, y + cfg.y);
            }
            pos.needsUpdate = true;
            geo.computeVertexNormals();

            const mat = new THREE.MeshStandardMaterial({
                color: cfg.color,
                flatShading: true,
                transparent: true,
                opacity: cfg.op,
                roughness: 0.9,
                metalness: 0,
                side: THREE.DoubleSide,
            });
            const mesh = new THREE.Mesh(geo, mat);
            mesh.position.z = -3;
            this.scene.add(mesh);
            this.terrainLayers.push(mesh);
        });

        this.turbines = [];
        const tPos = [
            [-2.5, 1.2, -3], [0, 1.6, -2.5], [2.5, 1.4, -3.5],
            [-1.2, 1.8, -1.8], [3.8, 0.9, -4.5],
        ];
        if (!PERF.lowPerf) tPos.push([-4, 0.8, -5], [5, 1.0, -4]);

        tPos.forEach(([x, y, z]) => {
            const t = this.createTurbine(0.7);
            t.position.set(x, y, z);
            const dist = -(z + 2);
            t.scale.setScalar(0.6 + dist * 0.06);
            this.scene.add(t);
            this.turbines.push(t);
        });

        if (!PERF.lowPerf) {
            const count = PERF.mobile ? 80 : 250;
            const g = new THREE.BufferGeometry();
            const p = new Float32Array(count * 3);
            const s = new Float32Array(count);
            for (let i = 0; i < count; i++) {
                p[i * 3] = (Math.random() - 0.5) * 18;
                p[i * 3 + 1] = Math.random() * 3.5;
                p[i * 3 + 2] = -2 - Math.random() * 6;
                s[i] = 0.3 + Math.random() * 1.5;
            }
            g.setAttribute('position', new THREE.BufferAttribute(p, 3));
            g.setAttribute('size', new THREE.BufferAttribute(s, 1));
            const m = new THREE.PointsMaterial({
                color: 0x99ddbb,
                transparent: true,
                opacity: 0.08,
                size: 0.6,
                sizeAttenuation: true,
                blending: THREE.AdditiveBlending,
                depthWrite: false,
            });
            this.mist = new THREE.Points(g, m);
            this.scene.add(this.mist);
            this.mistData = { positions: p };
        }

        if (!PERF.lowPerf) {
            const sc = PERF.mobile ? 80 : 300;
            const sg = new THREE.BufferGeometry();
            const sp = new Float32Array(sc * 3);
            for (let i = 0; i < sc; i++) {
                sp[i * 3] = (Math.random() - 0.5) * 50;
                sp[i * 3 + 1] = (Math.random() - 0.5) * 20 + 6;
                sp[i * 3 + 2] = -8 - Math.random() * 20;
            }
            sg.setAttribute('position', new THREE.BufferAttribute(sp, 3));
            const sm = new THREE.PointsMaterial({
                color: 0xaaeecc,
                transparent: true,
                opacity: 0.35,
                size: 0.07,
                sizeAttenuation: true,
            });
            this.stars = new THREE.Points(sg, sm);
            this.scene.add(this.stars);
        }

        this.camera.position.set(0, 1.2, 5.5);
        this.cameraBaseX = 0;
        this.camDrift = 0;
    }

    createTurbine(s) {
        const g = new THREE.Group();
        const tower = new THREE.Mesh(
            new THREE.CylinderGeometry(0.05 * s, 0.09 * s, 1.4 * s, 6),
            new THREE.MeshStandardMaterial({ color: 0x667788, roughness: 0.6, metalness: 0.3 })
        );
        tower.position.y = 0.7 * s;
        g.add(tower);

        const nacelle = new THREE.Mesh(
            new THREE.BoxGeometry(0.22 * s, 0.12 * s, 0.12 * s),
            new THREE.MeshStandardMaterial({ color: 0x99aabb, roughness: 0.5, metalness: 0.2 })
        );
        nacelle.position.set(0, 1.4 * s, 0);
        g.add(nacelle);

        const rotor = new THREE.Group();
        rotor.position.set(0.1 * s, 1.4 * s, 0);
        const bm = new THREE.MeshStandardMaterial({ color: 0xccddee, roughness: 0.7, metalness: 0.1 });
        for (let i = 0; i < 3; i++) {
            const blade = new THREE.Mesh(
                new THREE.BoxGeometry(0.6 * s, 0.025 * s, 0.05 * s),
                bm
            );
            blade.position.x = 0.3 * s;
            blade.rotation.z = (i / 3) * Math.PI * 2;
            rotor.add(blade);
        }
        g.add(rotor);
        g.userData.rotor = rotor;
        return g;
    }

    update(dt) {
        this.turbines.forEach(t => {
            if (t.userData.rotor) t.userData.rotor.rotation.x += dt * 2.5;
        });

        if (this.mist && this.mistData) {
            const pos = this.mist.geometry.attributes.position;
            const arr = this.mistData.positions;
            for (let i = 0; i < pos.count; i++) {
                arr[i * 3] += dt * 0.03;
                if (arr[i * 3] > 9) arr[i * 3] = -9;
                pos.setXYZ(i, arr[i * 3], arr[i * 3 + 1], arr[i * 3 + 2]);
            }
            pos.needsUpdate = true;
        }

        this.camDrift += dt * 0.05;
        this.camera.position.x = Math.sin(this.camDrift) * 1.2;
        this.camera.lookAt(0, 0.4, -1.5);
    }

    onScroll(progress) {
        super.onScroll(progress);
        this.camera.position.y = 1.2 - progress * 0.8;
    }
}

class GlobeScene extends SectionScene {
    init() {
        const ambient = new THREE.AmbientLight(0x224433, 0.6);
        this.scene.add(ambient);
        const dir1 = new THREE.DirectionalLight(0x88ccaa, 1.2);
        dir1.position.set(5, 5, 5);
        this.scene.add(dir1);
        const dir2 = new THREE.DirectionalLight(0xaadd88, 0.5);
        dir2.position.set(-3, -1, -3);
        this.scene.add(dir2);

        const detail = PERF.lowPerf ? 1 : (PERF.mobile ? 2 : 3);
        const geo = new THREE.IcosahedronGeometry(1.8, detail);

        const wireMat = new THREE.MeshBasicMaterial({
            color: 0x3fb872,
            wireframe: true,
            transparent: true,
            opacity: 0.12,
        });
        this.globe = new THREE.Mesh(geo, wireMat);
        this.scene.add(this.globe);

        const ppos = new Float32Array(geo.attributes.position.array);
        const pGeo = new THREE.BufferGeometry();
        pGeo.setAttribute('position', new THREE.BufferAttribute(ppos, 3));
        const pMat = new THREE.PointsMaterial({
            color: 0x6dd499,
            size: 0.05,
            sizeAttenuation: true,
            transparent: true,
            opacity: 0.9,
            blending: THREE.AdditiveBlending,
        });
        this.points = new THREE.Points(pGeo, pMat);
        this.scene.add(this.points);

        if (!PERF.lowPerf) {
            const verts = [];
            for (let i = 0; i < geo.attributes.position.count; i++) {
                verts.push(new THREE.Vector3(
                    geo.attributes.position.getX(i),
                    geo.attributes.position.getY(i),
                    geo.attributes.position.getZ(i)
                ));
            }
            const lg = new THREE.Group();
            const lc = PERF.mobile ? 25 : 70;
            for (let l = 0; l < lc; l++) {
                const i = Math.floor(Math.random() * verts.length);
                let j = Math.floor(Math.random() * verts.length);
                const d = verts[i].distanceTo(verts[j]);
                if (d > 0.4 && d < 2.5) {
                    const line = new THREE.Line(
                        new THREE.BufferGeometry().setFromPoints([verts[i], verts[j]]),
                        new THREE.LineBasicMaterial({ color: 0x3fb872, transparent: true, opacity: 0.06 })
                    );
                    lg.add(line);
                }
            }
            this.scene.add(lg);
            this.lines = lg;
        }

        const glow = new THREE.Mesh(
            new THREE.SphereGeometry(1.95, 24, 24),
            new THREE.MeshBasicMaterial({
                color: 0x3fb872,
                transparent: true,
                opacity: 0.04,
                side: THREE.BackSide,
            })
        );
        this.scene.add(glow);

        this.camera.position.set(0, 0.3, 4.5);
    }

    update(dt) {
        const s = dt * 0.2;
        this.globe.rotation.y += s;
        this.points.rotation.y += s;
        if (this.lines) this.lines.rotation.y += s;
    }
}

class ParticleScene extends SectionScene {
    init() {
        const count = PERF.lowPerf ? 200 : (PERF.mobile ? 500 : 1000);
        const geo = new THREE.BufferGeometry();
        const pos = new Float32Array(count * 3);
        const col = new Float32Array(count * 3);
        this.vels = [];

        for (let i = 0; i < count; i++) {
            pos[i * 3] = (Math.random() - 0.5) * 12;
            pos[i * 3 + 1] = (Math.random() - 0.5) * 8;
            pos[i * 3 + 2] = (Math.random() - 0.5) * 6;

            const sh = 0.3 + Math.random() * 0.7;
            col[i * 3] = 0.1 * sh;
            col[i * 3 + 1] = 0.5 * sh;
            col[i * 3 + 2] = 0.25 * sh;

            this.vels.push({
                x: (Math.random() - 0.5) * 0.25,
                y: (Math.random() - 0.5) * 0.25,
                z: (Math.random() - 0.5) * 0.15,
            });
        }

        geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        geo.setAttribute('color', new THREE.BufferAttribute(col, 3));

        const mat = new THREE.PointsMaterial({
            size: PERF.lowPerf ? 0.04 : 0.035,
            vertexColors: true,
            transparent: true,
            opacity: 0.55,
            blending: THREE.AdditiveBlending,
            sizeAttenuation: true,
            depthWrite: false,
        });

        this.system = new THREE.Points(geo, mat);
        this.scene.add(this.system);
        this.camera.position.set(0, 0, 5);
    }

    update(dt) {
        const pos = this.system.geometry.attributes.position;
        for (let i = 0; i < pos.count; i++) {
            const v = this.vels[i];
            let x = pos.getX(i) + v.x * dt;
            let y = pos.getY(i) + v.y * dt;
            let z = pos.getZ(i) + v.z * dt;
            if (x > 6) x = -6; if (x < -6) x = 6;
            if (y > 4) y = -4; if (y < -4) y = 4;
            if (z > 3) z = -3; if (z < -3) z = 3;
            pos.setXYZ(i, x, y, z);
        }
        pos.needsUpdate = true;
    }
}

function init() {
    const scenes = [];

    try {
        const hero = document.querySelector('#hero');
        if (hero) scenes.push(new HeroScene(hero, { camY: 1.2, camZ: 5.5 }));
    } catch (e) { console.warn('Hero 3D init failed:', e); }

    try {
        const mission = document.querySelector('#mission');
        if (mission) scenes.push(new GlobeScene(mission, { camY: 0.3, camZ: 4.5 }));
    } catch (e) { console.warn('Mission 3D init failed:', e); }

    try {
        const tech = document.querySelector('#technology');
        if (tech) scenes.push(new ParticleScene(tech, { camY: 0, camZ: 5 }));
    } catch (e) { console.warn('Tech 3D init failed:', e); }

    if (scenes.length === 0) return;

    function onScroll() {
        scenes.forEach(scene => {
            const r = scene.el.getBoundingClientRect();
            const vh = window.innerHeight;
            const p = Math.max(0, Math.min(1, (vh - r.top) / (vh + r.height)));
            scene.onScroll(p);
        });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => scenes.forEach(s => s.resize()), 150);
    });

    document.addEventListener('visibilitychange', () => {
        scenes.forEach(s => { s.running = !document.hidden; });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
