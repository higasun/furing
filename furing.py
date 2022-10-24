# MacOS Big Sur以降で動かすための設定
# Special settings for working on MacOS Big Sur or later
from math import radians
import platform
import ctypes.util
from tkinter.tix import WINDOW
from turtle import color

uname = platform.uname()
if uname.system == "Darwin" and uname.release >= "20.":
    _find_library = ctypes.util.find_library

    def find_library(name):
        if name in ["OpenGL"]:
            return "/System/Library/Frameworks/{0}.framework/{0}".format(name)
        return _find_library(name)

    ctypes.util.find_library = find_library

# 必要なパッケージのインポート
# Import required packages
import os
import sys
import glfw
import pyrr
import numpy as np
import ctypes
import open3d as o3d
from OpenGL.GL import *
from OpenGL.GLU import *
import simpleaudio

WIN_WIDTH = 500  # ウィンドウの幅 / Window width
WIN_HEIGHT = 500  # ウィンドウの高さ / Window height
WIN_TITLE = "OpenGL Course"  # ウィンドウのタイトル / Window title

# シェーダ言語のソースファイル / Shader source files
VERT_SHADER_FILE = os.path.join(os.path.dirname(__file__), "shaders", "render.vert")
FRAG_SHADER_FILE = os.path.join(os.path.dirname(__file__), "shaders", "render.frag")

# メッシュモデルのファイル
# Mesh model file
MESH_FILE = os.path.join(os.path.dirname(__file__), "data", "furin.obj")

# サウンドファイル
source_long = simpleaudio.WaveObject.from_wave_file("data/chiring_long.wav")
source_short = simpleaudio.WaveObject.from_wave_file("data/chiring_short.wav")
soundCnt = 0

# 頂点番号配列の大きさ
# Length of index array buffer
indexBufferSize = 0
indexBufferSizeGlass = 3 * 1072
indexBufferSizeJiku = 3 * 250
indexBufferSizeTanzaku = 3 * 24

# バッファを参照する番号
# Indices for vertex/index buffers
vaoId = 0
vertexBufferId = 0
indexBufferId = 0

# シェーダプログラムを参照する番号
# Index for a shader program
programId = 0

# オブジェクトを選択するためのID
# Index for identifying selected object
selectMode = False

# 立方体の回転角度
# Rotation angle for animating a cube
theta = 0
velTheta = 0.0
vel0Theta = 1.5
thresTheta = 8
cnt = 0
period = 300
windMode = False
soundFlg = True
rotVec = [1.0, 0.0, 0.0]
phai = 0

# モデルの色
colors = [
    [0.23, 0.47, 0.65], # 水
    [0.35, 0.47, 0.25], # 緑
    [0.67, 0.62, 0.35], # カーキ
    [0.41, 0.23,  0.5], # インディゴ
    [0.63, 0.46, 0.4], # サーモン
]
glassCdx = 0
tanzakuCdx = 1


# 背景のパラメータ
# yapf: disable
bg_positions = [
    [ -1.0, -1.0,  0.999 ],
    [  1.0, -1.0,  0.999 ],
    [ -1.0,  1.0,  0.999 ],
    [  1.0,  1.0,  0.999 ],
]

bg_colors = [
    [ 0.9, 0.9, 0.9 ],  # 白
    [ 0.9, 0.9, 0.9 ],  # 白
    [ 0.53, 0.74, 0.87 ],  # sky blue
    [ 0.9, 0.9, 0.9 ],  # 白
    [ 0.53, 0.74, 0.87 ],  # sky blue
    [ 0.53, 0.74, 0.87 ],  # sky blue
]

bg_faces = [
    [ 0, 1, 2 ],
    [ 1, 2, 3 ],
]
# yapf: enable


# VAOの初期化
# Initialize VAO
def initVAO():
    global vaoId, vertexBufferId, indexBufferId, indexBufferSize

    # メッシュファイルの読み込み
    # Load mesh file
    mesh = o3d.io.read_triangle_mesh(MESH_FILE)
    vertices = np.array(mesh.vertices, dtype='float32')
    indices = np.array(mesh.triangles, dtype='uint32')


    # 配列を1次元配列に変換しておく
    # Convert each array to 1D array
    vertices = np.array(vertices, dtype='float32').reshape((-1))
    indices = np.array(indices, dtype='uint32').reshape((-1))


    # VAOの作成
    # Create VAO
    vaoId = glGenVertexArrays(1)
    glBindVertexArray(vaoId)

    # 頂点バッファオブジェクトの作成
    # Create vertex buffer object
    vertexBufferId = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vertexBufferId)
    glBufferData(GL_ARRAY_BUFFER, len(vertices.tobytes()), vertices.tobytes(), GL_STATIC_DRAW)

    # 頂点バッファに対する属性情報の設定
    # Setup attributes for vertex buffer object
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 4 * 3, ctypes.c_void_p(0))

    # 頂点番号バッファオブジェクトの作成
    # Create index buffer object
    indexBufferId = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, indexBufferId)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices.tobytes()), indices.tobytes(), GL_STATIC_DRAW)

    # 頂点バッファのサイズを変数に入れておく
    # Store size of index array buffer
    indexBufferSize = len(indices)

    # VAOをOFFにしておく
    # Temporarily disable VAO
    glBindVertexArray(0)


# シェーダのソースファイルをコンパイルする
# Compile a shader source
def compileShader(filename, type):
    # シェーダの作成
    # Create a shader
    shaderId = glCreateShader(type)

    # ファイルをすべて読んで変数に格納
    # Load entire contents of a file and store to a string variable
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    # コードのコンパイル
    # Compile a source code
    glShaderSource(shaderId, code)
    glCompileShader(shaderId)

    # コンパイルの成否を判定する
    # Check whther compile is successful
    compileStatus = glGetShaderiv(shaderId, GL_COMPILE_STATUS)
    if compileStatus == GL_FALSE:
        # エラーメッセージの長さを取得する
        # Get length of error message
        errMsg = glGetShaderInfoLog(shaderId)

        # エラーメッセージとソースコードの出力
        # Print error message and corresponding source code
        sys.stderr.write("[ ERROR ] %s\n" % errMsg)
        sys.stderr.write("%s\n" % code)

        # コンパイルが失敗したらエラーメッセージとソースコードを表示して終了
        # Terminate with error message if compilation failed
        raise Exception("Failed to compile a shader!")

    return shaderId


# シェーダプログラムのビルド (=コンパイル＋リンク)
# Build a shader program (build = compile + link)
def buildShaderProgram(vShaderFile, fShaderFile):
    # 各種シェーダのコンパイル
    # Compile shader files
    vertShaderId = compileShader(vShaderFile, GL_VERTEX_SHADER)
    fragShaderId = compileShader(fShaderFile, GL_FRAGMENT_SHADER)

    # シェーダプログラムへのリンク
    # Link shader objects to the program
    programId = glCreateProgram()
    glAttachShader(programId, vertShaderId)
    glAttachShader(programId, fragShaderId)
    glLinkProgram(programId)

    # リンクの成否を判定する
    # Check whether link is successful
    linkState = glGetProgramiv(programId, GL_LINK_STATUS)
    if linkState == GL_FALSE:
        # エラーメッセージを取得する
        # Get error message
        errMsg = glGetProgramInfoLog(programId)

        # エラーメッセージを出力する
        # Print error message
        sys.stderr.write("[ ERROR ] %s\n" % errMsg)

        # リンクに失敗したらエラーメッセージを表示して終了
        # Terminate with error message if link is failed
        raise Exception("Failed to link shaders!")

    # シェーダを無効化した後にIDを返す
    # Disable shader program and return its ID
    glUseProgram(0)
    return programId


# シェーダの初期化
# Initialization related to shader programs
def initShaders():
    global programId
    programId = buildShaderProgram(VERT_SHADER_FILE, FRAG_SHADER_FILE)


# ユーザ定義のOpenGLの初期化
# User-define OpenGL initialization
def initializeGL():
    # 深度テストの有効化
    # Enable depth testing
    glEnable(GL_DEPTH_TEST)

    # 背景色の設定 (黒)
    # Background color (black)
    glClearColor(0.0, 0.0, 0.0, 1.0)

    # VAOの初期化
    # Initialize VAO
    initVAO()

    # 混合処理
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    # シェーダの用意
    # Prepare shader program
    initShaders()


def paintGL():
    global velTheta
    # 背景色の描画
    # Fill background color
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # 座標の変換
    # Coordinate transformation
    projMat = pyrr.matrix44.create_perspective_projection(45.0, WIN_WIDTH / WIN_HEIGHT, 0.1, 1000.0)
    viewMat = pyrr.matrix44.create_look_at(
        [1.0, 0.1, 1.0],  # 視点の位置
        [0.0, 0.0, 0.0],  # 見ている先
        [0.0, 1.0, 0.0])  # 視界の上方向

    # シェーダの有効化
    # Enable shader program
    glUseProgram(programId)

    # VAOの有効化
    # Enable VAO
    glBindVertexArray(vaoId)

    # オフセット
    offset = 0

    glEnable(GL_BLEND)
    glDisable(GL_DEPTH_TEST)
    # ガラス部分の描画
    if True:
        # 座標変換行列
        # Transformation matrices
        modelMat = np.eye(4)
        modelMat = np.dot(pyrr.matrix44.create_from_translation([0.0, 0.45, 0.0]), modelMat)
        modelMat = np.dot(pyrr.matrix44.create_from_axis_rotation(rotVec, np.radians(0.5*theta)), modelMat)
        modelMat = np.dot(pyrr.matrix44.create_from_translation([0.0, -0.45, 0.0]), modelMat)
        
        mvpMat = np.dot(modelMat, np.dot(viewMat, projMat))

        # Uniform変数の設定
        # Setup uniform variables

        # 番号1にして描画 (セレクトモードなら-1)
        if selectMode:
            glDisable(GL_BLEND)
            glEnable(GL_DEPTH_TEST)

            uid = glGetUniformLocation(programId, "u_selectID")
            glUniform1i(uid, 1)
        else:
            uid = glGetUniformLocation(programId, "u_selectID")
            glUniform1i(uid, -1)

        uid = glGetUniformLocation(programId, "u_color")
        glUniform4fv(uid, 1, colors[glassCdx] + [0.65])

        uid = glGetUniformLocation(programId, "u_mvpMat")
        glUniformMatrix4fv(uid, 1, GL_FALSE, mvpMat)

        glDrawElements(GL_TRIANGLES, indexBufferSizeGlass, GL_UNSIGNED_INT, ctypes.c_void_p(offset))

        offset += 4 * indexBufferSizeGlass

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

    # 軸部分の描画
    if True:
        # 座標変換行列
        # Transformation matrices
        #modelMat = np.eye(4)
        modelMat = pyrr.matrix44.create_from_translation([0.0, 0.45, 0.0])
        modelMat = np.dot(pyrr.matrix44.create_from_axis_rotation(rotVec, np.radians(theta)), modelMat)
        modelMat = np.dot(pyrr.matrix44.create_from_translation([0.0, -0.45, 0.0]), modelMat)
        
        mvMat = np.dot(modelMat, viewMat)
        mvpMat = np.dot(modelMat, np.dot(viewMat, projMat))

        # Uniform変数の設定
        # Setup uniform variables

        # 番号2にして描画 
        uid = glGetUniformLocation(programId, "u_selectID")
        glUniform1i(uid, 2 if selectMode else -1)

        uid = glGetUniformLocation(programId, "u_color")
        glUniform4fv(uid, 1, [0.9, 0.9, 0.9, 1.0])


        uid = glGetUniformLocation(programId, "u_mvpMat")
        glUniformMatrix4fv(uid, 1, GL_FALSE, mvpMat)

        glDrawElements(GL_TRIANGLES, indexBufferSizeJiku, GL_UNSIGNED_INT, ctypes.c_void_p(offset))

        offset += 4 * indexBufferSizeJiku

    # 短冊部分の描画
    if True:
        # 座標変換行列
        # Transformation matrices
        R = 0.45 * np.sin(np.radians(theta))

        modelMat = np.eye(4)
        modelMat = np.dot(pyrr.matrix44.create_from_translation([R * np.sin(np.radians(phai)), 0.45 * (1 - np.cos(np.radians(theta))), -R * np.cos(np.radians(phai))]), modelMat)
        modelMat = np.dot(pyrr.matrix44.create_from_axis_rotation(rotVec, np.radians(1.8 * theta)), modelMat)
        modelMat = np.dot(pyrr.matrix44.create_from_axis_rotation([0.0, 1.0, 0.0], np.radians(15.0 * theta)), modelMat)
        
        mvpMat = np.dot(modelMat, np.dot(viewMat, projMat))


        # Uniform変数の設定
        # Setup uniform variables

        # 短冊を番号3にして描画 
        uid = glGetUniformLocation(programId, "u_selectID")
        glUniform1i(uid, 3 if selectMode else -1)

        uid = glGetUniformLocation(programId, "u_color")
        glUniform4fv(uid, 1, colors[tanzakuCdx] + [1.0])

        uid = glGetUniformLocation(programId, "u_mvpMat")
        glUniformMatrix4fv(uid, 1, GL_FALSE, mvpMat)

    
        glDrawElements(GL_TRIANGLES, indexBufferSizeTanzaku, GL_UNSIGNED_INT, ctypes.c_void_p(offset))

        offset += 4 * indexBufferSizeTanzaku


    # VAOの無効化
    # Disable VAO
    glBindVertexArray(0)

    # シェーダの無効化
    # Disable shader program
    glUseProgram(0)




# ウィンドウサイズ変更のコールバック関数
# Callback function for window resizing
def resizeGL(window, width, height):
    global WIN_WIDTH, WIN_HEIGHT

    # ユーザ管理のウィンドウサイズを変更
    # Update user-managed window size
    WIN_WIDTH = width
    WIN_HEIGHT = height

    # GLFW管理のウィンドウサイズを変更
    # Update GLFW-managed window size
    glfw.set_window_size(window, WIN_WIDTH, WIN_HEIGHT)

    # 実際のウィンドウサイズ (ピクセル数) を取得
    # Get actual window size by pixels
    renderBufferWidth, renderBufferHeight = glfw.get_framebuffer_size(window)

    # ビューポート変換の更新
    # Update viewport transform
    glViewport(0, 0, renderBufferWidth, renderBufferHeight)


# マウスのクリックを処理するコールバック関数
# Callback for mouse click events
def mouseEvent(window, button, action, mods):
    global selectMode, windMode, glassCdx, tanzakuCdx

    if action == glfw.PRESS:
        # クリックされた位置を取得
        # Obtain click position
        px, py = glfw.get_cursor_pos(window)
        cx, cy = int(px), int(py)

        # 選択モードでの描画
        # Draw cubes with selection mode
        selectMode = True
        paintGL()
        selectMode = False

        # ピクセルの大きさの計算 (Macの場合には必要)
        # Calculate pixel size (required for Mac)
        renderBufferWidth, renderBufferHeight = glfw.get_framebuffer_size(window)
        pixelSize = max(renderBufferWidth / WIN_WIDTH, renderBufferHeight / WIN_HEIGHT)

        # より適切なやり方 (1ピクセルだけを読む)
        # Appropriate buffer access (read only a single pixel)
        byte = glReadPixels(cx * pixelSize, (WIN_HEIGHT - cy - 1) * pixelSize, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
        byte = np.frombuffer(byte, dtype='uint8')

        if button == glfw.MOUSE_BUTTON_RIGHT:
            if byte[0] == 1:
                glassCdx = (glassCdx + 1) % len(colors)
            elif byte[0] == 3:
                tanzakuCdx = (tanzakuCdx + 1) % len(colors)
        elif button == glfw.MOUSE_BUTTON_LEFT:
            if byte[0] > 0:
                windMode = True


# アニメーションのためのアップデート
# Update for animating object
def animate():
    global theta, velTheta,  cnt, vel0Theta, period, windMode, rotVec, phai

    if windMode:

        if cnt == 0:
            vel0Theta = np.random.uniform(low=0.7, high=1.4)
            phai = np.random.random() * 360
            rotVec = [np.cos(np.radians(phai)), 0.0, np.sin(np.radians(phai))]
        cnt += 1
        velTheta = vel0Theta * np.cos(2 * np.pi * cnt / 80)
        theta += velTheta

        # theta 減衰
        vel0Theta *= 0.994

        # 550 フレームでwindMode 終了
        if cnt >= 550 or (abs(theta) < 1e-1 and abs(velTheta) < 1e-2):
            windMode = False
            cnt = 0
            vel0Theta = 1.5
            theta = 0
            
# サウンド再生
def sound():
    global theta, thresTheta, windMode, source_short, source_long, soundCnt, soundFlg
    
    if not windMode: return

    if soundFlg and abs(theta) >= thresTheta:
        soundFlg = False
        soundCnt += 1
        if soundCnt % 2 == 0:
            source_long.play()
        else:
            source_short.play()
    elif abs(theta) < thresTheta:
        soundFlg = True





def main():
    # OpenGLを初期化する
    # OpenGL initialization
    if glfw.init() == glfw.FALSE:
        raise Exception("Initialization failed!")

    # OpenGLのバージョン設定 (Macの場合には必ず必要)
    # Specify OpenGL version (mandatory for Mac)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    # Windowの作成
    # Create a window
    #glfw.window_hint(glfw.DECORATED, glfw.FALSE)
    window = glfw.create_window(WIN_WIDTH, WIN_HEIGHT, "", None, None)
    if window is None:
        glfw.terminate()
        raise Exception("Window creation failed!")

    # OpenGLの描画対象にwindowを指定
    # Specify window as an OpenGL context
    glfw.make_context_current(window)

    # OpenGLのバージョンをチェック
    # Check OpenGL version
    print(glGetString(GL_VERSION).decode('ascii'))

    # ウィンドウのリサイズを扱う関数の登録
    # Register a callback function for window resizing
    glfw.set_window_size_callback(window, resizeGL)

     # マウスのイベントを処理する関数を登録
    # Register a callback function for mouse click events
    glfw.set_mouse_button_callback(window, mouseEvent)

    # ユーザ指定の初期化
    # User-specified initialization
    initializeGL()


    # メインループ
    # Main loop
    while glfw.window_should_close(window) == glfw.FALSE:
        # 描画 / Draw
        paintGL()

        # アニメーション / Animation
        animate()

        # サウンド
        sound()

        # 描画用バッファの切り替え
        # Swap drawing target buffers
        glfw.swap_buffers(window)
        glfw.poll_events()

    # 後処理 / Postprocess
    glfw.destroy_window(window)
    glfw.terminate()


if __name__ == "__main__":
    main()