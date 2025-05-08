import time
import random
from experta import *
exeTimes = 30  # 程序运行的总时间（秒）

class TrafficLights(KnowledgeEngine):
    """
    交通灯专家系统类
    使用基于规则的专家系统来控制交通灯的状态
    """
    
    @DefFacts()
    def _initial_action(self):
        """
        定义初始事实
        这些事实在系统启动时被添加到知识库中
        """
        yield Fact(Ticks = 0)                # 系统时钟计数（每0.1秒增加1）
        yield Fact(Second = 0)               # 实际秒数计数
        yield Fact(ASecond = False)          # 标记是否已经过了一秒
        yield Fact(SwitchTime = 5)           # 交通灯切换时间点（秒）
        yield Fact(Period = 10)              # 交通灯周期（秒）
        yield Fact(NSLight = 'GREEN')        # 北南方向交通灯状态（初始为绿灯）
        yield Fact(WELight = 'RED')          # 东西方向交通灯状态（初始为红灯）
        yield Fact(NSCars = 0)               # 北南方向车辆计数
        yield Fact(WECars = 0)               # 东西方向车辆计数
        yield Fact(YellowDuration = 2)       # 黄灯持续时间（秒）
    
    @Rule(AS.oldFact << Fact(Ticks = MATCH.times))
    def ticks(self, times, oldFact):
        """
        系统时钟规则
        每0.1秒触发一次，更新系统时钟
        当达到设定的总运行时间时，停止系统
        """
        self.retract(oldFact)                # 移除旧的时钟事实
        self.declare(Fact(Ticks = times + 1))  # 添加新的时钟事实
        time.sleep(0.1)                      # 暂停0.1秒
        if times == exeTimes * 10:           # 如果达到总运行时间（exeTimes秒）
            print('bye!')                    # 打印结束信息
            self.halt()                      # 停止系统
        else:
            if times % 10 == 0:              # 每10个时钟周期（1秒）
                self.declare(Fact(ASecond = True))  # 标记已经过了一秒
            self.comm()                      # 调用通信函数，模拟车辆到达

    @Rule(AS.fact1 << Fact(Second=MATCH.times),
          AS.fact2 << Fact(ASecond = True),
          salience= 1
    )
    def step(self, times, fact1, fact2):
        """
        秒计数规则
        当ASecond为True时触发，更新实际秒数
        """
        self.retract(fact1)                  # 移除旧的秒数事实
        self.retract(fact2)                  # 移除ASecond事实
        self.declare(Fact(Second= times + 1))  # 添加新的秒数事实
        print("{}-*-".format(times))         # 打印当前秒数

    @Rule(AS.fact1 << Fact(Second=MATCH.times),
          Fact(Period = MATCH.period),
          TEST(lambda times,period: times == period),
          AS.fact2 << Fact(NSCars = MATCH.nsCars),
          AS.fact3 << Fact(WECars = MATCH.weCars),
          AS.fact4 << Fact(SwitchTime= MATCH.switchTime),
          salience = 2
         )
    def startSwitch1(self, fact1, fact2, fact3, fact4, nsCars, weCars, switchTime, period):
        """
        周期结束切换规则
        当一个周期结束时触发，决定下一个周期的切换时间
        """
        self.retract(fact1)                  # 移除旧的秒数事实
        self.retract(fact2)                  # 移除北南方向车辆计数事实
        self.retract(fact3)                  # 移除东西方向车辆计数事实
        self.retract(fact4)                  # 移除切换时间事实
        self.decision(nsCars, weCars, switchTime, period)  # 根据车辆数量决定新的切换时间
        self.declare(Fact(Second = 0))       # 重置秒数
        self.declare(Fact(Switch = True))    # 标记需要切换交通灯
        self.declare(Fact(NSCars = 0))       # 重置北南方向车辆计数
        self.declare(Fact(WECars = 0))       # 重置东西方向车辆计数

    @Rule(
          Fact(Second = MATCH.times),
          Fact(SwitchTime = MATCH.switchTime),
          TEST(lambda switchTime,times:times == switchTime),
          salience= 2
       )
    def startSwitch2(self):
        """
        切换时间点规则
        当达到切换时间点时触发，标记需要切换交通灯
        """
        self.declare(Fact(Switch = True))    # 标记需要切换交通灯
        
    @Rule(
        AS.oldSwtich << Fact(Switch = True),
        AS.oldNS << Fact(NSLight = 'RED'),
        AS.oldWE << Fact(WELight = 'GREEN'),
        salience = 2
      )
    def switch1(self, oldSwtich, oldNS, oldWE): 
        """
        北南方向切换规则
        当北南方向为红灯，东西方向为绿灯，且需要切换时触发
        将北南方向切换为黄灯，东西方向切换为红灯
        """
        # 先切换到黄灯
        self.declare(Fact(NSLight = 'YELLOW'))  # 北南方向变为黄灯
        self.declare(Fact(WELight = 'RED'))     # 东西方向变为红灯
        self.retract(oldSwtich)                 # 移除切换标记
        self.retract(oldWE)                     # 移除旧的东西方向灯状态
        self.retract(oldNS)                     # 移除旧的北南方向灯状态
        # 设置黄灯计时器
        self.declare(Fact(YellowTimer = 0))     # 初始化黄灯计时器
        
    @Rule(
        AS.oldSwtich << Fact(Switch = True),
        AS.oldNS << Fact(NSLight = 'GREEN'),
        AS.oldWE << Fact(WELight = 'RED'),
        salience = 2
      )
    def switch2(self, oldSwtich, oldNS, oldWE):
        """
        东西方向切换规则
        当北南方向为绿灯，东西方向为红灯，且需要切换时触发
        将北南方向切换为红灯，东西方向切换为黄灯
        """
        # 先切换到黄灯
        self.declare(Fact(NSLight = 'RED'))     # 北南方向变为红灯
        self.declare(Fact(WELight = 'YELLOW'))  # 东西方向变为黄灯
        self.retract(oldSwtich)                 # 移除切换标记
        self.retract(oldWE)                     # 移除旧的东西方向灯状态
        self.retract(oldNS)                     # 移除旧的北南方向灯状态
        # 设置黄灯计时器
        self.declare(Fact(YellowTimer = 0))     # 初始化黄灯计时器
        
    @Rule(
        AS.oldNS << Fact(NSLight = 'YELLOW'),
        AS.oldWE << Fact(WELight = 'RED'),
        AS.oldTimer << Fact(YellowTimer = MATCH.timer),
        Fact(YellowDuration = MATCH.duration),
        TEST(lambda timer, duration: timer >= duration),
        salience = 3
    )
    def switchFromYellowNS(self, oldNS, oldWE, oldTimer):
        """
        北南方向黄灯结束规则
        当北南方向为黄灯，东西方向为红灯，且黄灯时间已到时触发
        将北南方向切换为红灯，东西方向切换为绿灯
        """
        self.declare(Fact(NSLight = 'RED'))     # 北南方向变为红灯
        self.declare(Fact(WELight = 'GREEN'))   # 东西方向变为绿灯
        self.retract(oldNS)                     # 移除旧的北南方向灯状态
        self.retract(oldWE)                     # 移除旧的东西方向灯状态
        self.retract(oldTimer)                  # 移除黄灯计时器
        
    @Rule(
        AS.oldNS << Fact(NSLight = 'RED'),
        AS.oldWE << Fact(WELight = 'YELLOW'),
        AS.oldTimer << Fact(YellowTimer = MATCH.timer),
        Fact(YellowDuration = MATCH.duration),
        TEST(lambda timer, duration: timer >= duration),
        salience = 3
    )
    def switchFromYellowWE(self, oldNS, oldWE, oldTimer):
        """
        东西方向黄灯结束规则
        当北南方向为红灯，东西方向为黄灯，且黄灯时间已到时触发
        将北南方向切换为绿灯，东西方向切换为红灯
        """
        self.declare(Fact(NSLight = 'GREEN'))   # 北南方向变为绿灯
        self.declare(Fact(WELight = 'RED'))     # 东西方向变为红灯
        self.retract(oldNS)                     # 移除旧的北南方向灯状态
        self.retract(oldWE)                     # 移除旧的东西方向灯状态
        self.retract(oldTimer)                  # 移除黄灯计时器
        
    @Rule(
        AS.oldTimer << Fact(YellowTimer = MATCH.timer),
        AS.fact1 << Fact(Second = MATCH.times),
        AS.fact2 << Fact(ASecond = True),
        salience = 4
    )
    def incrementYellowTimer(self, timer, times, oldTimer, fact1, fact2):
        """
        黄灯计时器增加规则
        当ASecond为True时触发，增加黄灯计时器的值
        """
        self.retract(oldTimer)                 # 移除旧的黄灯计时器
        self.retract(fact1)                    # 移除旧的秒数事实
        self.retract(fact2)                    # 移除ASecond事实
        self.declare(Fact(YellowTimer = timer + 1))  # 增加黄灯计时器
        self.declare(Fact(Second = times + 1))  # 增加秒数
        
    @Rule(
        Fact(NSLight = MATCH.NScolor),
        Fact(WELight = MATCH.WEcolor),
        salience = 2
      )
    def show(self, NScolor, WEcolor):
        """
        显示规则
        当交通灯状态变化时触发，显示当前交通灯状态
        """
        # 根据北南方向和东西方向的交通灯状态显示不同的图案
        if NScolor == 'RED' and WEcolor == 'RED':
            print('-X-  -X-')                  # 两个方向都是红灯
        elif NScolor == 'RED' and WEcolor == 'GREEN':
            print('-X-  -V-')                  # 北南红灯，东西绿灯
        elif NScolor == 'RED' and WEcolor == 'YELLOW':
            print('-X-  -Y-')                  # 北南红灯，东西黄灯
        elif NScolor == 'GREEN' and WEcolor == 'RED':
            print('-V-  -X-')                  # 北南绿灯，东西红灯
        elif NScolor == 'YELLOW' and WEcolor == 'RED':
            print('-Y-  -X-')                  # 北南黄灯，东西红灯
        elif NScolor == 'GREEN' and WEcolor == 'YELLOW':
            print('-V-  -Y-')                  # 北南绿灯，东西黄灯
        elif NScolor == 'YELLOW' and WEcolor == 'GREEN':
            print('-Y-  -V-')                  # 北南黄灯，东西绿灯
        elif NScolor == 'GREEN' and WEcolor == 'GREEN':
            print('-V-  -V-')                  # 两个方向都是绿灯
        elif NScolor == 'YELLOW' and WEcolor == 'YELLOW':
            print('-Y-  -Y-')                  # 两个方向都是黄灯

    @Rule(
        AS.fact1 << Fact(NSSign = True),
        AS.fact2 << Fact(NSCars = MATCH.cars)
    )
    def countNS(self, fact1, fact2, cars):
        """
        北南方向车辆计数规则
        当NSSign为True时触发，增加北南方向车辆计数
        """
        self.retract(fact1)                    # 移除NSSign事实
        self.retract(fact2)                    # 移除旧的北南方向车辆计数
        self.declare(Fact(NSCars = cars + 1))  # 增加北南方向车辆计数

    @Rule(
        AS.fact1 << Fact(WESign = True),
        AS.fact2 << Fact(WECars = MATCH.cars)
    )
    def countWE(self, fact1, fact2, cars):
        """
        东西方向车辆计数规则
        当WESign为True时触发，增加东西方向车辆计数
        """
        self.retract(fact1)                    # 移除WESign事实
        self.retract(fact2)                    # 移除旧的东西方向车辆计数
        self.declare(Fact(WECars = cars + 1))  # 增加东西方向车辆计数

    def decision(self, nsCars, weCars, switchTime, period):
        """
        决策函数
        根据北南方向和东西方向的车辆数量决定新的切换时间
        """
        if nsCars == 0:
            nsCars = 1                         # 避免除以零
        if weCars == 0:
            weCars = 1                         # 避免除以零
        # 根据车辆比例计算新的切换时间
        newSwitchTime = int(nsCars/(nsCars+weCars)* period)
        if newSwitchTime == 0:
            newSwitchTime = 1                  # 确保切换时间至少为1秒
        if newSwitchTime == period:
            newSwitchTime = period - 1         # 确保切换时间小于周期

        # 打印决策信息
        print('nsCars ={} and weCars={},so we changed switch time from {} to {}'.format(nsCars,weCars,switchTime,newSwitchTime))
        self.declare(Fact(SwitchTime = newSwitchTime))  # 设置新的切换时间
        
    def comm(self):
        """
        通信函数
        模拟车辆到达，随机生成北南方向和东西方向的车辆
        """
        if random.randint(0,5) == 0:           # 1/6的概率北南方向有车辆到达
            self.declare(Fact(NSSign = True))
        if random.randint(0,5) == 0:           # 1/6的概率东西方向有车辆到达
            self.declare(Fact(WESign = True))

def main(args = None):
    """
    主函数
    创建并运行交通灯专家系统
    """
    engine = TrafficLights()                   # 创建交通灯专家系统实例
    engine.reset()                             # 重置知识库
    engine.run()                               # 运行专家系统

if __name__ == "__main__":
    main()                                     # 如果直接运行此文件，则执行main函数