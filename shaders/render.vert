#version 330

// Attribute変数: 頂点の持つ属性情報(位置や色など)を表す
// Attribute variables: specifies vertex attributes, e.g., positions and colors.
layout(location = 0) in vec3 in_position;


// 各種変換行列 / Transformation matrices
uniform mat4 u_mvpMat;


void main() {
    // gl_Positionは必ず指定する
    // You MUST specify gl_Position
    gl_Position = u_mvpMat * vec4(in_position, 1.0);
}