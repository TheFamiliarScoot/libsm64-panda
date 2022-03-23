#version 150

uniform sampler2D p3d_Texture0;

// Input from vertex shader
in vec2 texcoord;
in vec4 vcolor;

// Output to the screen
out vec4 p3d_FragColor;

void main() {
  vec4 color = texture(p3d_Texture0, texcoord);
  
  float vcolor_base = (1.0 - color.a);
  vec4 colored = vec4(vcolor.bgr * vcolor_base, 1);
  vec4 alpha_plus_color = vec4(colored.b, colored.g, colored.r, 1.0);
  
  p3d_FragColor = alpha_plus_color + (color * color.a);
}