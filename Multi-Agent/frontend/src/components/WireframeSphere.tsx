"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function WireframeSphere() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Dimensions
    const width = container.clientWidth || 700;
    const height = container.clientHeight || 700;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 2000);
    camera.position.z = 650;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Group to hold all 3D objects
    const sphereGroup = new THREE.Group();
    scene.add(sphereGroup);

    // 1. Dark Translucent Core Sphere
    const coreGeo = new THREE.SphereGeometry(170, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x171412,
      transparent: true,
      opacity: 0.85,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    sphereGroup.add(coreMesh);

    // 2. Outer Geometric Polygon / Icosahedron Wireframe
    const icoGeo = new THREE.IcosahedronGeometry(210, 2);
    const wireframeGeo = new THREE.WireframeGeometry(icoGeo);
    
    // Primary Copper Lines
    const lineMatPrimary = new THREE.LineBasicMaterial({
      color: 0xb45309, // Copper Brown #B45309
      transparent: true,
      opacity: 0.35,
    });
    const linesPrimary = new THREE.LineSegments(wireframeGeo, lineMatPrimary);
    sphereGroup.add(linesPrimary);

    // Secondary Warm Copper Outer Mesh
    const outerIcoGeo = new THREE.IcosahedronGeometry(235, 1);
    const outerWireframe = new THREE.WireframeGeometry(outerIcoGeo);
    const lineMatSecondary = new THREE.LineBasicMaterial({
      color: 0xd97706, // Warm Copper #D97706
      transparent: true,
      opacity: 0.22,
    });
    const linesSecondary = new THREE.LineSegments(outerWireframe, lineMatSecondary);
    sphereGroup.add(linesSecondary);

    // 3. Orbital Rings
    const createRing = (radius: number, color: number, opacity: number, rx: number, ry: number) => {
      const ringGeo = new THREE.TorusGeometry(radius, 0.8, 16, 100);
      const ringMat = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = rx;
      ringMesh.rotation.y = ry;
      return ringMesh;
    };

    const ring1 = createRing(260, 0xb45309, 0.25, Math.PI / 3, Math.PI / 6);
    const ring2 = createRing(290, 0xd97706, 0.18, -Math.PI / 4, Math.PI / 4);
    const ring3 = createRing(320, 0x78350f, 0.15, Math.PI / 6, -Math.PI / 3);

    sphereGroup.add(ring1);
    sphereGroup.add(ring2);
    sphereGroup.add(ring3);

    // 4. Muted Copper Node Particles
    const posArray = icoGeo.attributes.position.array;
    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute("position", new THREE.BufferAttribute(posArray, 3));

    const particleMat = new THREE.PointsMaterial({
      size: 4.5,
      color: 0xd97706, // #D97706
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
    });
    const particleSystem = new THREE.Points(particleGeo, particleMat);
    sphereGroup.add(particleSystem);

    // Ambient Lighting
    const ambientLight = new THREE.AmbientLight(0xb45309, 0.5);
    scene.add(ambientLight);

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      // Slow continuous rotations
      sphereGroup.rotation.y += 0.0012;
      sphereGroup.rotation.x += 0.0004;

      linesPrimary.rotation.y += 0.0006;
      linesSecondary.rotation.y -= 0.0008;

      ring1.rotation.z += 0.001;
      ring2.rotation.z -= 0.0012;
      ring3.rotation.z += 0.0008;

      particleSystem.rotation.y += 0.0012;

      renderer.render(scene, camera);
    };

    animate();

    // Responsive Resize Handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("resize", handleResize);

    // Cleanup on unmount
    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animId);
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
      coreGeo.dispose();
      coreMat.dispose();
      icoGeo.dispose();
      outerIcoGeo.dispose();
      lineMatPrimary.dispose();
      lineMatSecondary.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="no-print"
      style={{
        position: "fixed",
        top: "-60px",
        right: "-60px",
        width: "720px",
        height: "720px",
        pointerEvents: "none",
        zIndex: 0,
        opacity: 0.35,
        overflow: "hidden",
      }}
    />
  );
}
