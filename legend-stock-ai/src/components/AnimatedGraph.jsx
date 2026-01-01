

// File: AnimatedGraph.jsx
import React, { useRef, useEffect } from "react";
import "./AnimatedGraph.css";

const NUM_POINTS = 100;
const NUM_LINES = 3;
const LINE_COLORS = ["#00fff7", "#ff00f7", "#8400ff"];
const LINE_WIDTHS = [1.5, 1.2, 1.4];

export default function AnimatedGraph() {
  const canvasRef = useRef(null);

useEffect(() => {
  const canvas = canvasRef.current;
  const ctx = canvas.getContext("2d");

  const resizeCanvas = () => {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  };
  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  const width = canvas.width;
  const height = canvas.height;
  const spacing = width / (NUM_POINTS - 1);

  // 💡 Initialize with gently randomized starting values
  const lines = Array.from({ length: NUM_LINES }).map(() => {
    let base = height / 2;
    return Array.from({ length: NUM_POINTS }, () => {
      base += (Math.random() - 0.5) * 15;
      return Math.max(0, Math.min(height, base));
    });
  });

  const draw = () => {
    ctx.clearRect(0, 0, width, height);
    lines.forEach((line, i) => {
      ctx.beginPath();
      ctx.strokeStyle = LINE_COLORS[i % LINE_COLORS.length];
      ctx.lineWidth = LINE_WIDTHS[i % LINE_WIDTHS.length];
      ctx.shadowColor = LINE_COLORS[i % LINE_COLORS.length];
      ctx.shadowBlur = 15;

      line.forEach((y, index) => {
        const x = index * spacing;
        index === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });

      ctx.stroke();
    });
  };

  const update = () => {
    for (let i = 0; i < NUM_LINES; i++) {
      lines[i].shift();
      const lastY = lines[i][lines[i].length - 1];
      const newY = lastY + (Math.random() - 0.5) * 20;
      lines[i].push(Math.max(0, Math.min(height, newY)));
    }
  };

  const animate = () => {
    update();
    draw();
    requestAnimationFrame(animate);
  };

  animate();

  return () => window.removeEventListener("resize", resizeCanvas);
}, []);


  return (
    <div className="graph-wrapper">
      <canvas ref={canvasRef} className="graph-canvas" />
    </div>
  );
}
