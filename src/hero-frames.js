// Source coordinates measured in player-flight-keyed.png (1536 × 1024).
// Generated artwork is NOT a regular grid. Register the rigid waist/armor,
// not the silhouette bounds. Leg geometry now stays on a fixed pose frame.
// Each entry is [cropX, cropY, width, height, waistX, waistY].
export const HERO_FRAMES = [
  [
    [150, 32, 205, 338, 250, 197],
    [489, 32, 207, 341, 590, 197],
    [822, 32, 204, 338, 923, 197],
    [1160, 32, 206, 336, 1261, 197],
  ],
  [
    [150, 373, 225, 312, 291, 525],
    [501, 373, 212, 306, 633, 525],
    [822, 373, 222, 312, 961, 525],
    [1165, 373, 212, 312, 1294, 525],
  ],
  [
    [148, 693, 211, 307, 221, 851],
    [513, 693, 202, 307, 590, 851],
    [821, 693, 210, 307, 896, 851],
    [1165, 693, 212, 308, 1241, 851],
  ],
];

// Neutral source frame 4 and right-bank source frame 2 swap the extended
// leg/thruster. Exclude those drawing inconsistencies and ping-pong the
// remaining three frames to keep the same four-beat animation cadence.
export const HERO_FRAME_ORDER = [
  [0, 1, 2, 1],
  [0, 2, 3, 2],
  [0, 1, 2, 3],
];

export function installHeroAnimation(material) {
  const uniforms = {
    heroFrameOffset: {value: [0, 0]},
    heroWaistY: {value: 0},
    heroPulse: {value: 1},
  };
  material.userData.heroAnimation = uniforms;
  material.customProgramCacheKey = () => 'hero-stable-legs-v1';
  material.onBeforeCompile = shader => {
    Object.assign(shader.uniforms, uniforms);
    shader.fragmentShader = `uniform vec2 heroFrameOffset;
uniform float heroWaistY;
uniform float heroPulse;
${shader.fragmentShader}`.replace('#include <map_fragment>', `
      vec4 fixedPose = texture2D(map, vMapUv);
      vec4 animatedUpper = texture2D(map, vMapUv + heroFrameOffset);
      // End the animated region above the hips. Blend only across torso
      // armor, so neither knees nor the foot nozzles switch source frames.
      float upperMask = smoothstep(heroWaistY + 32.0/1024.0,
                                   heroWaistY + 44.0/1024.0, vMapUv.y);
      vec4 heroColor = mix(fixedPose, animatedUpper, upperMask);
      if(heroColor.g>.25 && heroColor.g>heroColor.r*1.3 && heroColor.g>heroColor.b*1.3) discard;
      // Exhaust flicker changes light, not the pose or direction of a jet.
      if(vMapUv.y < heroWaistY && heroColor.b > .38 &&
         heroColor.b > heroColor.r*1.05 && heroColor.b > heroColor.g*1.2 && heroColor.r > .18)
        heroColor.rgb *= heroPulse;
      diffuseColor *= heroColor;
    `);
  };
}

export function applyHeroFrame(sprite, texture, row, phase) {
  const column = HERO_FRAME_ORDER[row][phase];
  const [x, y, width, height, waistX, waistY] = HERO_FRAMES[row][0];
  const animatedFrame = HERO_FRAMES[row][column];
  const uniforms = sprite.material.userData.heroAnimation;
  if (uniforms) {
    uniforms.heroFrameOffset.value[0] = (animatedFrame[4] - waistX) / 1536;
    uniforms.heroFrameOffset.value[1] = (waistY - animatedFrame[5]) / 1024;
    uniforms.heroWaistY.value = 1 - waistY / 1024;
    uniforms.heroPulse.value = [1, 1.08, 1, .92][phase];
  }
  texture.repeat.set(width / 1536, height / 1024);
  texture.offset.set(x / 1536, 1 - (y + height) / 1024);
  // Keep pixel scale constant: a shorter flame must not enlarge the body.
  sprite.scale.set(width * 2.45 / 248, height * 3.65 / 337, 1);
  // Sprite.center is measured bottom-up. The gameplay position and rotation
  // pivot remain at the same waist point across every frame and stance.
  sprite.center.set((waistX - x) / width, 1 - (waistY - y) / height);
}
