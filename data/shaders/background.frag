#version 330 core
#define FRAG_COLOUR     0
in VertexData
{
    vec2    uvs;
    vec4    rgba;
} fs_in;

layout  (location = FRAG_COLOUR, index = 0) out vec4 fragColor;
uniform float time;
float hash( float n ) { return fract(sin(n)*753.5453123); }
float noise( in vec3 x )
{
    vec3 p = floor(x);
    vec3 f = fract(x);
    f = f*f*f*(3.0-2.0*f);

    float n = p.x + p.y*157.0 + 113.0*p.z;
    return mix(mix(mix( hash(n+  0.0), hash(n+  1.0),f.x),
                   mix( hash(n+157.0), hash(n+158.0),f.x),f.y),
               mix(mix( hash(n+113.0), hash(n+114.0),f.x),
                   mix( hash(n+270.0), hash(n+271.0),f.x),f.y),f.z);
}
float n ( vec3 x ) {
	float s = noise(x);
    for (float i = 2.; i < 10.; i++) {
    	s += noise(x/i)/i;

    }
    return s;
}
// makes a wierd void effect in the background
// kinda purple, looks cool!
void main()
{
    float scale = 20.;
    float a = abs(n(vec3((fs_in.uvs*scale)+time*3.14,sin(time)))-n(vec3((fs_in.uvs*scale)+time,cos(time+3.))));
	fragColor = vec4(.7-pow(a, .8), .4-pow(a, .0)/2., 1.-pow(a, .8), 1);
}