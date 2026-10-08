/* Receipt-driven canvas renderer, loaded only on the Plinko page. */
(() => {
  "use strict";
  globalThis.RedPlinko = {create({id, multiple}) {
    const canvas = id("plinkoCanvas");
    const width = 720,
      height = 510,
      pegRadius = 3.5,
      ballRadius = 8;
    let board,
      layer,
      ctx,
      key = "",
      balls = [],
      resting = null;
    let frameId = null,
      timeoutId,
      lastHit = -1,
      warned = false;

    function cancelFrames() {
      if (frameId !== null && typeof cancelAnimationFrame === "function")
        cancelAnimationFrame(frameId);
      frameId = null;
      clearTimeout(timeoutId);
    }

    function unavailable(error) {
      cancelFrames();
      for (const ball of balls) ball.done?.();
      balls = [];
      if (!warned) {
        warned = true;
        console.warn(
          "PLINKO Animation unavailable; verified results and balances are still saved.",
          error,
        );
      }
      return false;
    }

    function slot(context, index, active = false) {
      const x = 360 + (index - board.rows / 2) * board.step;
      context.fillStyle = active
        ? "#fff2b6"
        : index < 2 || index > board.rows - 2
          ? "#a91f36"
          : "#672334";
      context.fillRect(x - board.step * 0.47, 438, board.step * 0.94, 38);
      context.fillStyle = active ? "#1b1020" : "#ffffff";
      const label = multiple(board.values[index]);
      let size = board.rows > 12 ? 10 : 12;
      context.font = `600 ${size}px sans-serif`;
      while (size > 6 && context.measureText(label).width > board.step * 0.84)
        context.font = `600 ${--size}px sans-serif`;
      context.textAlign = "center";
      context.fillText(label, x, 461);
    }

    function setBoard(rows, values) {
      if (!canvas) return false;
      try {
        const scale = Math.max(
          1,
          Math.min(
            2,
            ((canvas.getBoundingClientRect().width || width) / width) *
              (globalThis.devicePixelRatio || 1),
          ),
        );
        const nextKey = `${rows}:${values.join(",")}:${scale.toFixed(2)}`;
        if (key === nextKey && board) return true;
        const changed = board && (board.rows !== rows || board.values.join(',') !== values.join(','));
        // Resizing rebuilds only the cached pixels, preserving ball positions.
        // A genuinely different paytable finishes old presentations first.
        if (changed) {
          for (const ball of balls) ball.done?.();
          balls = []; resting = null; lastHit = -1;
          cancelFrames();
        }
        board = {
          rows,
          values,
          step: 620 / (rows + 1),
          top: 64,
          dy: 332 / (rows - 1),
        };
        canvas.width = Math.round(width * scale);
        canvas.height = Math.round(height * scale);
        ctx = canvas.getContext("2d");
        layer = document.createElement("canvas");
        layer.width = canvas.width;
        layer.height = canvas.height;
        const background = layer.getContext("2d");
        if (!ctx || !background) return unavailable("Canvas context missing");
        ctx.setTransform(scale, 0, 0, scale, 0, 0);
        background.setTransform(scale, 0, 0, scale, 0, 0);
        for (let r = 0; r < rows; r++) {
          for (let c = 0; c <= r; c++) {
            background.beginPath();
            background.arc(
              360 + (c - r / 2) * board.step,
              board.top + r * board.dy,
              pegRadius,
              0,
              2 * Math.PI,
            );
            background.fillStyle = "#e9d9de";
            background.fill();
          }
        }
        values.forEach((_, index) => slot(background, index));
        key = nextKey;
        return paint(performance.now());
      } catch (error) {
        key = "";
        return unavailable(error);
      }
    }

    function trajectory(result, now) {
      const points = [
        { x: 360, y: 18 },
        { x: 360, y: board.top - pegRadius - ballRadius },
      ];
      let right = 0;
      result.path.forEach((bit, row) => {
        right += bit;
        points.push({
          x: 360 + (right - (row + 1) / 2) * board.step,
          y:
            row === board.rows - 1
              ? 427
              : board.top + (row + 1) * board.dy - pegRadius - ballRadius,
        });
      });
      return {
        points,
        slot: result.slot,
        began: now,
        duration: 360 + (board.rows - 1) * 105,
      };
    }

    function sample(ball, now) {
      const elapsed = Math.max(0, Math.min(ball.duration, now - ball.began));
      let segment, t;
      if (elapsed < 180) {
        segment = 0;
        t = elapsed / 180;
      } else {
        const middle = (board.rows - 1) * 105;
        if (elapsed < 180 + middle) {
          segment = 1 + Math.floor((elapsed - 180) / 105);
          t = ((elapsed - 180) % 105) / 105;
        } else {
          segment = board.rows;
          t = Math.min(1, (elapsed - 180 - middle) / 180);
        }
      }
      const a = ball.points[segment],
        b = ball.points[segment + 1];
      const dy = b.y - a.y;
      // Contact points sit above each peg, not inside it. Each verified bit
      // sends the ball to the left/right peg using a short parabolic bounce.
      const rise = Math.min(5, dy * 0.2);
      const launch = 2 * rise + 2 * Math.sqrt(rise * (rise + dy));
      return {
        x: a.x + (b.x - a.x) * t,
        y:
          segment === 0
            ? a.y + dy * t * t
            : a.y - launch * t + (dy + launch) * t * t,
      };
    }

    function paint(now) {
      if (!ctx || !layer) return false;
      try {
        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(layer, 0, 0, width, height);
        if (lastHit >= 0) slot(ctx, lastHit, true);
        const positions = balls.map((ball) => sample(ball, now));
        if (resting && !balls.length) positions.push(resting);
        for (const position of positions) {
          ctx.beginPath();
          ctx.arc(position.x, position.y, ballRadius, 0, 2 * Math.PI);
          ctx.fillStyle = "#ff415b";
          ctx.shadowColor = "#ff415b";
          ctx.shadowBlur = 10;
          ctx.fill();
        }
        ctx.shadowBlur = 0;
        return true;
      } catch (error) {
        return unavailable(error);
      }
    }

    function finish() {
      const last = balls[balls.length - 1];
      if (last) {
        resting = last.points[last.points.length - 1];
        lastHit = last.slot;
      }
      for (const ball of balls) ball.done?.();
      balls = [];
      cancelFrames();
      paint(performance.now());
    }

    function frame() {
      frameId = null;
      try {
        // Use one monotonic clock. Older RAF timestamps and slow frames must
        // never rewind a ball or leave an animation waiting indefinitely.
        const now = performance.now();
        balls = balls.filter((ball) => {
          if (now - ball.began < ball.duration) return true;
          resting = ball.points[ball.points.length - 1];
          lastHit = ball.slot;
          ball.done?.();
          return false;
        });
        if (!paint(now)) return;
        if (balls.length && !document.hidden)
          frameId = requestAnimationFrame(frame);
        else finish();
      } catch (error) {
        unavailable(error);
      }
    }

    function drop(rows, values, result, done) {
      try {
        if (!setBoard(rows, values)) { done?.(); return; }
        const now = performance.now();
        balls.push({...trajectory(result, now), done});
        if (
          document.hidden ||
          globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ||
          typeof requestAnimationFrame !== "function"
        ) {
          finish();
          return;
        }
        if (frameId === null) frameId = requestAnimationFrame(frame);
        clearTimeout(timeoutId);
        timeoutId = setTimeout(finish, balls[balls.length - 1].duration + 400);
      } catch (error) {
        unavailable(error);
        done?.();
      }
    }

    if (canvas) {
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) finish();
      });
      window.addEventListener("pagehide", () => finish());
      let resizeId;
      window.addEventListener("resize", () => {
        clearTimeout(resizeId);
        resizeId = setTimeout(() => {
          if (board) setBoard(board.rows, board.values);
        }, 120);
      });
    }
    return { setBoard, drop };
  
  }};
})();
