############################  导库  ############################

# 显示窗口所需要的库
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

# 串口通信所需要的库
import serial
import threading
from queue import Queue

############################  串口  ############################

# 创建三个缓冲区
buffer_display = Buffer()   # 用于显示上方提示信息
buffer_output = Buffer()    # 用于显示从串口读入的数据
buffer_input = Buffer()     # 用于从用户读入要向串口写入的数据

# 串口参数设置
serialPort = "COM4" # 串口
baudRate = 9600     # 波特率
buffer_display.text = "输入`exit`退出程序，输入`1`或`0`控制交通灯亮灭\n"
buffer_display.text += "参数设置：串口=%s ，波特率=%d" % (serialPort, baudRate)

# 连接串口
try:
    ser = serial.Serial(serialPort, baudRate, timeout=0.5)
except:
    raise Exception("无法打开串口！请确保串口号正确，且设备已连接！")

# 创建输出队列，存储要向串口写入的数据
output_queue = Queue()

# 创建终止标志变量，用于Control-C退出时终止线程
stop_event = threading.Event()

# 读串口线程
def read_serial(event):
    while not event.is_set():
        try:
            # 读取串口数据
            data = ser.readline().decode('utf-8').rstrip()
            # 将读取的数据写入显示缓冲区
            if data:
                buffer_output.text += f"Received: {data}\n"
            if buffer_output.text.count('\n') > 5: # 限制显示行数
                buffer_output.text = buffer_output.text.split('\n', 1)[1]
        except Exception as e:
            pass
    print("Read Serial Exit!")

# 写串口线程
def write_serial(event):
    while not event.is_set():
        try:
            # 从输出队列中读取数据
            # [Note] 如果队列为空，会阻塞，直到有数据写入队列。因此要设置一个超时时间
            data = output_queue.get(timeout=0.5)
            # 将数据写入串口
            if data:
                ser.write(data)
        except Exception as e:
            pass
    print("Write Serial Exit!")

############################  显示  ############################

# 创建一个显示容器
root_container = HSplit([
    Window(height=2, content=BufferControl(buffer=buffer_display, focusable=False)),  # 上方提示信息
    Window(height=1, char='-'),  # 分割线
    Window(height=5, content=BufferControl(buffer=buffer_output, focusable=False)),  # 上方显示
    Window(height=1, char='-'),  # 分割线
    Window(height=1, content=BufferControl(buffer=buffer_input, focusable=True)),  # 下方指令输入
])
# 创建一个布局
layout = Layout(root_container)

# 绑定快捷键
kb = KeyBindings()
# 退出快捷键（Ctrl + C）
@kb.add('c-c')
def exit_(event):
    event.app.exit()  # 退出应用

# 回车快捷键（Enter）
@kb.add('enter')
def enter_(event):
    text = buffer_input.text.strip()
    if text == 'exit':
        exit_(event)
    # 将输入的数据写入缓冲区
    elif text == '1':
        output_queue.put(b"1")
        buffer_output.text += f"Sent: {text}\n"
    elif text == '0':
        output_queue.put(b"0")
        buffer_output.text += f"Sent: {text}\n"
    else:
        buffer_output.text += f"Error: Invalid input: {text}\n"
    # 清空输入缓冲区
    buffer_input.text = ""

# 创建终端应用
app = Application(layout=layout, key_bindings=kb, full_screen=True)


if __name__ == '__main__':
    # 启动线程
    t1 = threading.Thread(target=read_serial, args=(stop_event,))
    t2 = threading.Thread(target=write_serial, args=(stop_event,))
    t1.start()
    t2.start()
    app.run() # 阻塞
    # 退出后终止线程
    stop_event.set()
    # 关闭串口
    ser.close()
