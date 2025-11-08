// Mind-Blowing 3D World Showcase Features
// Add this script to your Nexus Hub HTML file

// ===== Prompt #10: 30-Second Spectacle =====
class SpectacleShowcase {
    constructor(worldInstance) {
        this.world = worldInstance;
        this.isPlaying = false;
        this.avatar = null;
        this.clones = [];
        this.particles = null;
        this.startTime = 0;
        this.animationFrame = null;
    }

    start() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        this.startTime = Date.now();
        this.world.showNotification('🎬 30-Second Spectacle Starting!');

        // Create the main avatar
        this.createSpectacleAvatar();

        // Start the choreographed sequence
        this.animate();
    }

    createSpectacleAvatar() {
        const avatarGroup = new THREE.Group();

        // Body
        const bodyGeometry = new THREE.CylinderGeometry(0.5, 0.5, 2, 16);
        const bodyMaterial = new THREE.MeshStandardMaterial({
            color: 0xff0000,
            emissive: 0xff0000,
            emissiveIntensity: 0.5,
            metalness: 0.8,
            roughness: 0.2
        });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.position.y = 1;
        avatarGroup.add(body);

        // Head
        const headGeometry = new THREE.SphereGeometry(0.4, 16, 16);
        const head = new THREE.Mesh(headGeometry, bodyMaterial.clone());
        head.position.y = 2.2;
        avatarGroup.add(head);

        // Arms
        const armGeometry = new THREE.CylinderGeometry(0.15, 0.15, 1.2);
        const leftArm = new THREE.Mesh(armGeometry, bodyMaterial.clone());
        leftArm.position.set(-0.7, 1, 0);
        leftArm.rotation.z = Math.PI / 4;
        avatarGroup.add(leftArm);

        const rightArm = new THREE.Mesh(armGeometry, bodyMaterial.clone());
        rightArm.position.set(0.7, 1, 0);
        rightArm.rotation.z = -Math.PI / 4;
        avatarGroup.add(rightArm);

        // Legs
        const legGeometry = new THREE.CylinderGeometry(0.15, 0.15, 1.2);
        const leftLeg = new THREE.Mesh(legGeometry, bodyMaterial.clone());
        leftLeg.position.set(-0.3, 0, 0);
        avatarGroup.add(leftLeg);

        const rightLeg = new THREE.Mesh(legGeometry, bodyMaterial.clone());
        rightLeg.position.set(0.3, 0, 0);
        avatarGroup.add(rightLeg);

        // Position in front of camera
        avatarGroup.position.set(0, 3, -10);
        avatarGroup.userData = { body, head, leftArm, rightArm, leftLeg, rightLeg, bodyMaterial };

        this.avatar = avatarGroup;
        this.world.scene.add(avatarGroup);

        // Start materialization effect
        this.materializeFromParticles();
    }

    materializeFromParticles() {
        // Create materialization particles
        const particleCount = 500;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount * 3; i += 3) {
            const radius = Math.random() * 3;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;

            positions[i] = this.avatar.position.x + radius * Math.sin(phi) * Math.cos(theta);
            positions[i + 1] = this.avatar.position.y + radius * Math.sin(phi) * Math.sin(theta);
            positions[i + 2] = this.avatar.position.z + radius * Math.cos(phi);

            colors[i] = Math.random();
            colors[i + 1] = Math.random();
            colors[i + 2] = Math.random();
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
            size: 0.1,
            vertexColors: true,
            transparent: true,
            opacity: 0.8
        });

        this.particles = new THREE.Points(geometry, material);
        this.world.scene.add(this.particles);

        // Animate particles converging
        const startTime = Date.now();
        const converge = () => {
            const elapsed = (Date.now() - startTime) / 1000;
            if (elapsed > 2) {
                this.world.scene.remove(this.particles);
                this.particles = null;
                return;
            }

            const positions = this.particles.geometry.attributes.position.array;
            for (let i = 0; i < positions.length; i += 3) {
                positions[i] += (this.avatar.position.x - positions[i]) * 0.1;
                positions[i + 1] += (this.avatar.position.y - positions[i + 1]) * 0.1;
                positions[i + 2] += (this.avatar.position.z - positions[i + 2]) * 0.1;
            }
            this.particles.geometry.attributes.position.needsUpdate = true;
            requestAnimationFrame(converge);
        };
        converge();
    }

    animate() {
        if (!this.isPlaying) return;

        const elapsed = (Date.now() - this.startTime) / 1000;

        // 30-second choreographed sequence
        if (elapsed < 3) {
            // 0-3s: Materialize and introduce (Red)
            this.setAvatarColor(0xff0000);
            this.avatar.rotation.y = elapsed * 2;
        } else if (elapsed < 6) {
            // 3-6s: Happy emotion (Orange)
            this.setAvatarColor(0xff8800);
            this.avatar.scale.setScalar(1 + Math.sin(elapsed * 10) * 0.2);
            this.avatar.position.y = 3 + Math.sin(elapsed * 5) * 0.5;
        } else if (elapsed < 9) {
            // 6-9s: Excited emotion (Yellow)
            this.setAvatarColor(0xffff00);
            this.avatar.rotation.y += 0.2;
            this.avatar.scale.setScalar(1.5 + Math.sin(elapsed * 15) * 0.3);
        } else if (elapsed < 12) {
            // 9-12s: Mega bounce (Green)
            this.setAvatarColor(0x00ff00);
            const bounceProgress = (elapsed - 9) / 3;
            this.avatar.position.y = 3 + Math.sin(bounceProgress * Math.PI) * 17; // Jump to y=20
            this.avatar.scale.setScalar(1.2);
        } else if (elapsed < 15) {
            // 12-15s: Ultra spin (Blue)
            this.setAvatarColor(0x0000ff);
            this.avatar.rotation.y += 0.5; // 10x rotation speed
            this.avatar.rotation.x = Math.sin(elapsed * 5) * 0.5;
            this.avatar.position.y = 3;
        } else if (elapsed < 18) {
            // 15-18s: Color transition through rainbow (Indigo)
            this.setAvatarColor(0x4b0082);
            this.avatar.rotation.y += 0.1;
        } else if (elapsed < 20) {
            // 18-20s: Violet
            this.setAvatarColor(0x9400d3);
        } else if (elapsed < 22) {
            // 20-22s: Spawn 50 clones
            if (this.clones.length === 0) {
                this.spawnClones();
            }
            this.animateClones(elapsed - 20);
        } else if (elapsed < 25) {
            // 22-25s: Synchronized wave dance
            this.synchronizedDance(elapsed - 22);
        } else if (elapsed < 28) {
            // 25-28s: Build up to explosion
            const intensity = (elapsed - 25) / 3;
            this.avatar.scale.setScalar(1 + intensity * 2);
            this.clones.forEach((clone, i) => {
                clone.scale.setScalar(1 + intensity * 2);
            });
        } else if (elapsed < 30) {
            // 28-30s: Particle supernova
            if (elapsed < 28.1) {
                this.createSupernova();
            }
        } else {
            // 30s: Show "NEXUS HUB" text and end
            this.showFinalText();
            this.stop();
            return;
        }

        this.animationFrame = requestAnimationFrame(() => this.animate());
    }

    setAvatarColor(color) {
        if (!this.avatar) return;
        const colorObj = new THREE.Color(color);
        this.avatar.children.forEach(child => {
            if (child.material) {
                child.material.color = colorObj;
                child.material.emissive = colorObj;
            }
        });
    }

    spawnClones() {
        const cloneCount = 50;
        const radius = 15;

        for (let i = 0; i < cloneCount; i++) {
            const clone = this.avatar.clone();
            const angle = (i / cloneCount) * Math.PI * 2;

            clone.position.x = Math.cos(angle) * radius;
            clone.position.y = 3;
            clone.position.z = Math.sin(angle) * radius;
            clone.rotation.y = -angle;
            clone.scale.setScalar(0.8);

            clone.userData.cloneIndex = i;
            this.clones.push(clone);
            this.world.scene.add(clone);
        }

        this.world.showNotification('✨ 50 Clones Spawned!');
    }

    animateClones(elapsed) {
        this.clones.forEach((clone, i) => {
            clone.rotation.y += 0.05;
            clone.position.y = 3 + Math.sin(elapsed * 3 + i * 0.1) * 0.5;
        });
    }

    synchronizedDance(elapsed) {
        const wavePhase = elapsed * 2;

        // Main avatar dances
        this.avatar.position.y = 3 + Math.sin(wavePhase * 2) * 1;
        this.avatar.rotation.y += 0.1;

        // Clones do synchronized wave
        this.clones.forEach((clone, i) => {
            const phase = wavePhase + (i / this.clones.length) * Math.PI * 2;
            clone.position.y = 3 + Math.sin(phase * 3) * 1.5;
            clone.rotation.y = Math.sin(phase) * 0.5;
            clone.scale.setScalar(0.8 + Math.sin(phase * 2) * 0.3);
        });
    }

    createSupernova() {
        // Remove avatar and clones
        if (this.avatar) {
            this.world.scene.remove(this.avatar);
        }
        this.clones.forEach(clone => this.world.scene.remove(clone));

        // Create massive particle explosion
        const particleCount = 2000;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const velocities = [];
        const colors = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;

            // Start at center
            positions[i3] = 0;
            positions[i3 + 1] = 3;
            positions[i3 + 2] = -10;

            // Random velocity
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;
            const speed = 0.5 + Math.random() * 1.5;

            velocities.push({
                x: Math.sin(phi) * Math.cos(theta) * speed,
                y: Math.sin(phi) * Math.sin(theta) * speed,
                z: Math.cos(phi) * speed
            });

            // Rainbow colors
            const hue = Math.random();
            const color = new THREE.Color().setHSL(hue, 1, 0.5);
            colors[i3] = color.r;
            colors[i3 + 1] = color.g;
            colors[i3 + 2] = color.b;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
            size: 0.2,
            vertexColors: true,
            transparent: true,
            opacity: 1,
            blending: THREE.AdditiveBlending
        });

        const supernova = new THREE.Points(geometry, material);
        this.world.scene.add(supernova);

        // Animate explosion
        const startTime = Date.now();
        const explode = () => {
            const elapsed = (Date.now() - startTime) / 1000;
            if (elapsed > 2) {
                this.world.scene.remove(supernova);
                return;
            }

            const positions = supernova.geometry.attributes.position.array;
            for (let i = 0; i < velocities.length; i++) {
                const i3 = i * 3;
                positions[i3] += velocities[i].x;
                positions[i3 + 1] += velocities[i].y;
                positions[i3 + 2] += velocities[i].z;
            }
            supernova.geometry.attributes.position.needsUpdate = true;
            supernova.material.opacity = 1 - (elapsed / 2);

            requestAnimationFrame(explode);
        };
        explode();

        this.world.showNotification('💥 SUPERNOVA!');
    }

    showFinalText() {
        // This would use TextGeometry if font is loaded
        // For now, show notification
        this.world.showNotification('🌟 NEXUS HUB - The Future of 3D Worlds! 🌟');
    }

    stop() {
        this.isPlaying = false;
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        if (this.avatar) {
            this.world.scene.remove(this.avatar);
        }
        this.clones.forEach(clone => this.world.scene.remove(clone));
        this.clones = [];
        this.avatar = null;
    }
}


// ===== Prompt #1: Emotion Symphony Orchestra =====
class EmotionSymphony {
    constructor(worldInstance) {
        this.world = worldInstance;
        this.isPlaying = false;
        this.avatars = [];
        this.particles = [];
        this.trailGroups = [];
        this.currentEmotion = 'neutral';
    }

    start() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        this.world.showNotification('🎵 Emotion Symphony Orchestra - Use mouse gestures to conduct!');

        this.createOrchestra();
        this.setupConductorControls();
    }

    createOrchestra() {
        const amphitheaterRadius = 20;
        const rows = 5;
        const avatarsPerRow = 20;
        const instruments = ['strings', 'brass', 'woodwinds', 'percussion'];
        const instrumentColors = {
            'strings': 0xff6b9d,     // Pink - Happy
            'brass': 0xffd700,       // Gold - Excited
            'woodwinds': 0x4169e1,   // Blue - Thinking
            'percussion': 0xff4500   // Orange Red - Surprised
        };

        for (let row = 0; row < rows; row++) {
            const rowRadius = amphitheaterRadius - (row * 3);
            const rowHeight = row * 2;
            const instrument = instruments[row % instruments.length];
            const color = instrumentColors[instrument];

            for (let i = 0; i < avatarsPerRow; i++) {
                const angle = (i / avatarsPerRow) * Math.PI * 2;
                const avatar = this.createInstrumentAvatar(instrument, color);

                avatar.position.x = Math.cos(angle) * rowRadius;
                avatar.position.y = rowHeight + 2;
                avatar.position.z = Math.sin(angle) * rowRadius;
                avatar.rotation.y = -angle;

                avatar.userData = {
                    instrument,
                    baseY: rowHeight + 2,
                    angle,
                    row,
                    index: i
                };

                this.avatars.push(avatar);
                this.world.scene.add(avatar);

                // Create particle trail group
                const trailGroup = new THREE.Group();
                trailGroup.position.copy(avatar.position);
                this.trailGroups.push(trailGroup);
                this.world.scene.add(trailGroup);
            }
        }

        this.world.showNotification(`🎭 100 musicians ready! Move your mouse to conduct different emotions!`);
    }

    createInstrumentAvatar(instrument, color) {
        const group = new THREE.Group();

        // Body
        const bodyGeometry = new THREE.CylinderGeometry(0.3, 0.3, 1, 8);
        const material = new THREE.MeshStandardMaterial({
            color: color,
            emissive: color,
            emissiveIntensity: 0.3,
            metalness: 0.6,
            roughness: 0.3
        });

        const body = new THREE.Mesh(bodyGeometry, material);
        body.position.y = 0.5;
        group.add(body);

        // Head
        const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 8), material.clone());
        head.position.y = 1.2;
        group.add(head);

        // Instrument indicator (shape varies by type)
        let instrumentMesh;
        if (instrument === 'strings') {
            // Violin shape
            instrumentMesh = new THREE.Mesh(
                new THREE.BoxGeometry(0.1, 0.3, 0.05),
                material.clone()
            );
        } else if (instrument === 'brass') {
            // Trumpet shape
            instrumentMesh = new THREE.Mesh(
                new THREE.ConeGeometry(0.1, 0.3, 8),
                material.clone()
            );
        } else if (instrument === 'woodwinds') {
            // Flute shape
            instrumentMesh = new THREE.Mesh(
                new THREE.CylinderGeometry(0.05, 0.05, 0.4),
                material.clone()
            );
        } else {
            // Drum shape
            instrumentMesh = new THREE.Mesh(
                new THREE.CylinderGeometry(0.15, 0.15, 0.1),
                material.clone()
            );
        }

        instrumentMesh.position.x = 0.3;
        instrumentMesh.position.y = 0.8;
        group.add(instrumentMesh);

        return group;
    }

    setupConductorControls() {
        // Map mouse position to emotions
        const onMouseMove = (event) => {
            if (!this.isPlaying) return;

            const x = (event.clientX / window.innerWidth) * 2 - 1;
            const y = -(event.clientY / window.innerHeight) * 2 + 1;

            // Quadrant-based emotion mapping
            if (x > 0 && y > 0) {
                this.conductEmotion('happy', 0xff6b9d);
            } else if (x > 0 && y < 0) {
                this.conductEmotion('excited', 0xffd700);
            } else if (x < 0 && y > 0) {
                this.conductEmotion('thinking', 0x4169e1);
            } else {
                this.conductEmotion('neutral', 0x888888);
            }
        };

        window.addEventListener('mousemove', onMouseMove);
        this.mouseMoveHandler = onMouseMove;
    }

    conductEmotion(emotion, color) {
        if (this.currentEmotion === emotion) return;

        this.currentEmotion = emotion;

        // Animate all avatars based on emotion
        this.avatars.forEach((avatar, index) => {
            const { instrument, baseY } = avatar.userData;

            // Different animation for each emotion
            if (emotion === 'happy') {
                avatar.children[0].material.color.setHex(0xff6b9d);
                avatar.children[0].material.emissive.setHex(0xff6b9d);
            } else if (emotion === 'excited') {
                avatar.children[0].material.color.setHex(0xffd700);
                avatar.children[0].material.emissive.setHex(0xffd700);
            } else if (emotion === 'thinking') {
                avatar.children[0].material.color.setHex(0x4169e1);
                avatar.children[0].material.emissive.setHex(0x4169e1);
            } else {
                avatar.children[0].material.color.setHex(0x888888);
                avatar.children[0].material.emissive.setHex(0x888888);
            }

            // Create particle trail
            this.createParticleTrail(avatar, color);
        });

        this.world.showNotification(`🎵 Emotion: ${emotion.toUpperCase()}`);
    }

    createParticleTrail(avatar, color) {
        const particleGeometry = new THREE.SphereGeometry(0.05, 4, 4);
        const particleMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.8
        });

        const particle = new THREE.Mesh(particleGeometry, particleMaterial);
        particle.position.copy(avatar.position);
        particle.userData = {
            velocity: new THREE.Vector3(
                (Math.random() - 0.5) * 0.1,
                Math.random() * 0.2,
                (Math.random() - 0.5) * 0.1
            ),
            life: 2
        };

        this.particles.push(particle);
        this.world.scene.add(particle);
    }

    update(deltaTime) {
        if (!this.isPlaying) return;

        const time = Date.now() / 1000;

        // Animate avatars
        this.avatars.forEach((avatar, index) => {
            const { baseY, row, angle } = avatar.userData;

            // Wave motion
            avatar.position.y = baseY + Math.sin(time * 2 + index * 0.1) * 0.3;

            // Rotation based on emotion
            if (this.currentEmotion === 'excited') {
                avatar.rotation.y += 0.02;
            } else {
                avatar.rotation.y = angle + Math.sin(time + index) * 0.1;
            }
        });

        // Update and remove old particles
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const particle = this.particles[i];
            particle.userData.life -= deltaTime;

            if (particle.userData.life <= 0) {
                this.world.scene.remove(particle);
                this.particles.splice(i, 1);
            } else {
                particle.position.add(particle.userData.velocity);
                particle.material.opacity = particle.userData.life / 2;
            }
        }
    }

    stop() {
        this.isPlaying = false;

        // Remove all avatars
        this.avatars.forEach(avatar => this.world.scene.remove(avatar));
        this.avatars = [];

        // Remove all particles
        this.particles.forEach(particle => this.world.scene.remove(particle));
        this.particles = [];

        // Remove trail groups
        this.trailGroups.forEach(group => this.world.scene.remove(group));
        this.trailGroups = [];

        // Remove event listener
        if (this.mouseMoveHandler) {
            window.removeEventListener('mousemove', this.mouseMoveHandler);
        }
    }
}


// ===== Prompt #4: Emotion Infection =====
class EmotionInfection {
    constructor(worldInstance) {
        this.world = worldInstance;
        this.isPlaying = false;
        this.avatars = [];
        this.infectTimer = null;
    }

    start() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        this.world.showNotification('😊 Emotion Infection: Watch joy spread like a virus!');

        this.createAvatarGrid();
        this.injectHappiness();
    }

    createAvatarGrid() {
        const gridSize = 10; // 10x10 = 100 avatars
        const spacing = 3;
        const startX = -(gridSize * spacing) / 2;
        const startZ = -(gridSize * spacing) / 2;

        for (let row = 0; row < gridSize; row++) {
            for (let col = 0; col < gridSize; col++) {
                const avatar = this.createSadAvatar();
                avatar.position.set(
                    startX + col * spacing,
                    2,
                    startZ + row * spacing
                );
                avatar.userData = {
                    row,
                    col,
                    emotion: 'sad',
                    infectionTime: null
                };

                this.avatars.push(avatar);
                this.world.scene.add(avatar);
            }
        }
    }

    createSadAvatar() {
        const group = new THREE.Group();

        // Body - slumped posture
        const bodyGeometry = new THREE.CylinderGeometry(0.4, 0.5, 1.5);
        const sadMaterial = new THREE.MeshStandardMaterial({
            color: 0x4169e1, // Blue = sad
            emissive: 0x000033,
            emissiveIntensity: 0.2,
            metalness: 0.3,
            roughness: 0.8
        });

        const body = new THREE.Mesh(bodyGeometry, sadMaterial);
        body.position.y = 0.75;
        body.rotation.x = 0.2; // Slumped forward
        group.add(body);

        // Head - looking down
        const head = new THREE.Mesh(new THREE.SphereGeometry(0.3, 8, 8), sadMaterial.clone());
        head.position.y = 1.6;
        head.position.z = -0.2;
        group.add(head);

        return group;
    }

    injectHappiness() {
        // Pick center avatar to start the infection
        const centerIndex = Math.floor(this.avatars.length / 2);
        this.infectAvatar(this.avatars[centerIndex]);

        // Start spreading
        this.infectTimer = setInterval(() => this.spreadInfection(), 200);
    }

    infectAvatar(avatar) {
        if (avatar.userData.emotion === 'happy') return;

        avatar.userData.emotion = 'happy';
        avatar.userData.infectionTime = Date.now();

        // Visual transformation
        const happyColor = 0xffd700; // Golden yellow
        avatar.children.forEach(child => {
            if (child.material) {
                child.material.color.setHex(happyColor);
                child.material.emissive.setHex(0xffaa00);
                child.material.emissiveIntensity = 0.5;
            }
            // Straighten posture
            if (child.geometry.type === 'CylinderGeometry') {
                child.rotation.x = 0;
            }
            if (child.geometry.type === 'SphereGeometry') {
                child.position.y = 1.8;
                child.position.z = 0;
            }
        });

        // Celebration particles
        this.createCelebrationBurst(avatar.position);
    }

    createCelebrationBurst(position) {
        const particleCount = 50;
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const velocities = [];

        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;
            positions[i3] = position.x;
            positions[i3 + 1] = position.y + 1;
            positions[i3 + 2] = position.z;

            const angle = (i / particleCount) * Math.PI * 2;
            const speed = 0.1 + Math.random() * 0.2;
            velocities.push({
                x: Math.cos(angle) * speed,
                y: Math.random() * 0.3,
                z: Math.sin(angle) * speed,
                life: 1
            });
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const material = new THREE.PointsMaterial({
            color: 0xffd700,
            size: 0.1,
            transparent: true,
            opacity: 1
        });

        const particles = new THREE.Points(geometry, material);
        this.world.scene.add(particles);

        // Animate burst
        const animateBurst = () => {
            const positions = particles.geometry.attributes.position.array;
            let allDead = true;

            for (let i = 0; i < velocities.length; i++) {
                if (velocities[i].life > 0) {
                    allDead = false;
                    const i3 = i * 3;
                    positions[i3] += velocities[i].x;
                    positions[i3 + 1] += velocities[i].y;
                    positions[i3 + 2] += velocities[i].z;
                    velocities[i].life -= 0.02;
                }
            }

            particles.geometry.attributes.position.needsUpdate = true;
            particles.material.opacity = Math.max(...velocities.map(v => v.life));

            if (!allDead) {
                requestAnimationFrame(animateBurst);
            } else {
                this.world.scene.remove(particles);
            }
        };
        animateBurst();
    }

    spreadInfection() {
        const happyAvatars = this.avatars.filter(a => a.userData.emotion === 'happy');
        const sadAvatars = this.avatars.filter(a => a.userData.emotion === 'sad');

        if (sadAvatars.length === 0) {
            clearInterval(this.infectTimer);
            this.world.showNotification('🎉 Complete! 100% happiness achieved!');
            return;
        }

        // Each happy avatar can infect nearby sad ones
        happyAvatars.forEach(happy => {
            sadAvatars.forEach(sad => {
                const distance = happy.position.distanceTo(sad.position);
                if (distance < 4) { // Infection radius
                    // Random chance to infect
                    if (Math.random() < 0.3) {
                        this.infectAvatar(sad);
                    }
                }
            });
        });

        // Update status
        const happyCount = happyAvatars.length;
        const percentage = Math.round((happyCount / this.avatars.length) * 100);
        this.world.showNotification(`😊 Happiness: ${percentage}% (${happyCount}/100 avatars)`);
    }

    update(deltaTime) {
        if (!this.isPlaying) return;

        const time = Date.now() / 1000;

        // Animate avatars
        this.avatars.forEach((avatar, index) => {
            if (avatar.userData.emotion === 'happy') {
                // Happy avatars bounce
                avatar.position.y = 2 + Math.sin(time * 3 + index * 0.2) * 0.3;
                avatar.rotation.y = Math.sin(time * 2 + index * 0.1) * 0.2;
            } else {
                // Sad avatars stay still
                avatar.position.y = 2;
            }
        });
    }

    stop() {
        this.isPlaying = false;
        if (this.infectTimer) {
            clearInterval(this.infectTimer);
        }

        this.avatars.forEach(avatar => this.world.scene.remove(avatar));
        this.avatars = [];
    }
}

// Export for use in main world
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SpectacleShowcase, EmotionSymphony, EmotionInfection };
}
