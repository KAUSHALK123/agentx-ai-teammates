import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export const ThreeCoreCanvas: React.FC<{ className?: string }> = ({ className }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 400;
    const height = container.clientHeight || 400;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 7.5);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x4f46e5, 3, 50);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x10b981, 2.5, 50);
    pointLight2.position.set(-5, -3, 3);
    scene.add(pointLight2);

    // Core Group
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Outer Wireframe Icosahedron
    const sphereGeo = new THREE.IcosahedronGeometry(1.5, 2);
    const sphereMat = new THREE.MeshPhongMaterial({
      color: 0x4f46e5,
      emissive: 0x312e81,
      wireframe: true,
      transparent: true,
      opacity: 0.85
    });
    const coreSphere = new THREE.Mesh(sphereGeo, sphereMat);
    coreGroup.add(coreSphere);

    // Inner Solid Orb
    const innerGeo = new THREE.SphereGeometry(0.85, 32, 32);
    const innerMat = new THREE.MeshPhongMaterial({
      color: 0x6366f1,
      emissive: 0x4338ca,
      shininess: 100
    });
    const innerOrb = new THREE.Mesh(innerGeo, innerMat);
    coreGroup.add(innerOrb);

    // Ring 1 (Indigo)
    const ringGeo1 = new THREE.TorusGeometry(2.3, 0.035, 16, 100);
    const ringMat1 = new THREE.MeshPhongMaterial({ color: 0x6366f1, emissive: 0x3730a3 });
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
    ring1.rotation.x = Math.PI / 3;
    coreGroup.add(ring1);

    // Ring 2 (Emerald)
    const ringGeo2 = new THREE.TorusGeometry(2.6, 0.03, 16, 100);
    const ringMat2 = new THREE.MeshPhongMaterial({ color: 0x10b981, emissive: 0x065f46 });
    const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
    ring2.rotation.y = Math.PI / 4;
    ring2.rotation.z = Math.PI / 6;
    coreGroup.add(ring2);

    // Orbiting Agent Satellites
    const nodeGeo = new THREE.SphereGeometry(0.18, 16, 16);
    const nodeMat1 = new THREE.MeshPhongMaterial({ color: 0x4f46e5, emissive: 0x3730a3 });
    const nodeMat2 = new THREE.MeshPhongMaterial({ color: 0x2563eb, emissive: 0x1d4ed8 });
    const nodeMat3 = new THREE.MeshPhongMaterial({ color: 0x9333ea, emissive: 0x6b21a8 });

    const node1 = new THREE.Mesh(nodeGeo, nodeMat1);
    const node2 = new THREE.Mesh(nodeGeo, nodeMat2);
    const node3 = new THREE.Mesh(nodeGeo, nodeMat3);
    coreGroup.add(node1);
    coreGroup.add(node2);
    coreGroup.add(node3);

    let targetRotX = 0;
    let targetRotY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      targetRotY = x * 0.4;
      targetRotX = -y * 0.4;
    };

    window.addEventListener('mousemove', handleMouseMove);

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || 400;
      const h = container.clientHeight || 400;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    let animationFrameId: number;
    const startTime = performance.now();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const t = (performance.now() - startTime) * 0.001;

      coreSphere.rotation.x += 0.005;
      coreSphere.rotation.y += 0.008;

      ring1.rotation.z += 0.008;
      ring1.rotation.x += 0.004;

      ring2.rotation.x -= 0.006;
      ring2.rotation.y += 0.005;

      innerOrb.scale.setScalar(1 + Math.sin(t * 2.2) * 0.05);

      node1.position.x = Math.cos(t * 1.2) * 2.3;
      node1.position.y = Math.sin(t * 1.2) * Math.cos(Math.PI / 3) * 2.3;
      node1.position.z = Math.sin(t * 1.2) * Math.sin(Math.PI / 3) * 2.3;

      node2.position.x = Math.cos(t * 0.9 + 2.1) * 2.6 * Math.cos(Math.PI / 4);
      node2.position.y = Math.sin(t * 0.9 + 2.1) * 2.6;
      node2.position.z = Math.cos(t * 0.9 + 2.1) * 2.6 * Math.sin(Math.PI / 4);

      node3.position.x = Math.sin(t * 1.4 + 4.2) * 2.0;
      node3.position.y = Math.cos(t * 1.4 + 4.2) * 2.0;
      node3.position.z = Math.sin(t * 1.4) * 1.2;

      coreGroup.rotation.y += (targetRotY - coreGroup.rotation.y) * 0.05;
      coreGroup.rotation.x += (targetRotX - coreGroup.rotation.x) * 0.05;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return <div ref={containerRef} className={className || 'w-full h-80'} />;
};
