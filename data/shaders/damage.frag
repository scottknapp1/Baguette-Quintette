#version 330 core
#define FRAG_COLOUR     0
in VertexData
{
    vec2    uvs;
    vec4    rgba;
} fs_in;

uniform vec3 rgb;
uniform vec3 differences;
uniform float time;
uniform sampler2D image;
layout  (location = FRAG_COLOUR, index = 0) out vec4 fragColor;

void main()
{
    float red = rgb[0] + time * differences[0];
    float green = rgb[1] + time * differences[1];
    float blue = rgb[2] + time * differences[2];

    fragColor = vec4(red, green, blue, fs_in.rgba.a) * texture(image, fs_in.uvs);
}
