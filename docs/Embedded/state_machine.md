## 什麼是 state machine?
state machine 是一種用來描述系統狀態轉換的模型。它由一組狀態、一組事件和一組轉換規則組成。當系統接收到某個事件時，它會根據當前狀態和事件來決定是否進行狀態轉換。
在嵌入式系統中，state machine 可以用來管理系統的不同狀態，例如開機、待機、工作等。它可以幫助我們清晰地定義系統的行為，並且使得系統更易於維護和擴展。

## 為什麼要使用 state machine?
使用 state machine 有以下幾個優點：
1. **清晰的狀態定義**：state machine 可以幫助我們清晰地定義系統的不同狀態，並且使得系統的行為更易於理解。
2. **易於維護**：當系統的行為需要修改時，我們只需要修改 state machine 的轉換規則，而不需要修改整個系統的代碼。
3. **易於擴展**：當系統需要新增狀態或事件時，我們只需要新增相應的狀態或事件，而不需要修改整個系統的代碼。
4. **可視化**：state machine 可以用圖形化的方式來表示，這樣可以更直觀地理解系統的行為。

## 如何實作 state machine?
實作 state machine 的基本步驟如下：
1. 定義狀態：首先，我們需要定義系統的不同狀態。每個狀態都應該有一個唯一的標識符。
2. 定義事件：接下來，我們需要定義系統可能接收到的事件。每個事件也應該有一個唯一的標識符。
3. 定義轉換規則：然後，我們需要定義狀態之間的轉換規則。每個轉換規則應該包含當前狀態、事件和下一個狀態。
4. 實作狀態機：最後，我們需要實作一個狀態機來管理狀態轉換。這個狀態機應該能夠接收事件，並根據當前狀態和事件來決定是否進行狀態轉換。
## 範例：簡單的 LED 控制器
以下是一個簡單的 LED 控制器的 state machine 範例。這個控制器有三個狀態：關閉、開啟和閃爍。它可以接收兩個事件：開啟和關閉，並根據當前狀態和事件來決定下一個狀態。
```c
#include <stdio.h>
#include <stdbool.h>
typedef enum {
    STATE_OFF,
    STATE_ON,
    STATE_BLINKING
} State;
typedef enum {
    EVENT_TURN_ON,
    EVENT_TURN_OFF,
    EVENT_BLINK
} Event;
typedef struct {
    State current_state;
} StateMachine;
void handle_event(StateMachine *sm, Event event) {
    switch (sm->current_state) {
        case STATE_OFF:
            if (event == EVENT_TURN_ON) {
                sm->current_state = STATE_ON;
                printf("LED is now ON\n");
            }
            break;
        case STATE_ON:
            if (event == EVENT_TURN_OFF) {
                sm->current_state = STATE_OFF;
                printf("LED is now OFF\n");
            } else if (event == EVENT_BLINK) {
                sm->current_state = STATE_BLINKING;
                printf("LED is now BLINKING\n");
            }
            break;
        case STATE_BLINKING:
            if (event == EVENT_TURN_OFF) {
                sm->current_state = STATE_OFF;
                printf("LED is now OFF\n");
            } else if (event == EVENT_TURN_ON) {
                sm->current_state = STATE_ON;
                printf("LED is now ON\n");
            }
            break;
    }
}
int main() {
    StateMachine sm = {STATE_OFF};
    handle_event(&sm, EVENT_TURN_ON); // LED is now ON
    handle_event(&sm, EVENT_BLINK);   // LED is now BLINKING
    handle_event(&sm, EVENT_TURN_OFF); // LED is now OFF
    handle_event(&sm, EVENT_TURN_ON); // LED is now ON
    handle_event(&sm, EVENT_BLINK);   // LED is now BLINKING
    handle_event(&sm, EVENT_TURN_OFF); // LED is now OFF
    return 0;
}
```
在這個範例中，我們定義了三個狀態（STATE_OFF、STATE_ON、STATE_BLINKING）和三個事件（EVENT_TURN_ON、EVENT_TURN_OFF、EVENT_BLINK）。我們實作了一個狀態機（StateMachine），它有一個當前狀態（current_state）。當接收到事件時，我們根據當前狀態和事件來決定下一個狀態，並輸出相應的訊息。
這個範例展示了如何使用 state machine 來管理系統的狀態轉換。通過定義狀態、事件和轉換規則，我們可以清晰地描述系統的行為，並且使得系統更易於維護和擴展。
## 結論
state machine 是一種強大的工具，可以用來管理嵌入式系統的狀態轉換。它可以幫助我們清晰地定義系統的行為，並且使得系統更易於維護和擴展。
通過定義狀態、事件和轉換規則，我們可以實作一個狀態機來管理系統的行為。這樣的設計不僅使得系統的行為更易於理解，還能提高系統的可維護性和可擴展性。
在實際應用中，state machine 可以用於各種場景，例如控制器、通訊協議、用戶界面等。它是一種非常有用的設計模式，值得在嵌入式系統開發中廣泛應用。
如果你對 state machine 有興趣，可以進一步研究相關的設計模式和實作方法。這將有助於你在嵌入式系統開發中更好地管理系統的狀態轉換，並提高系統的可靠性和可維護性。
## 參考資料
- [State Machine Design Patterns](https://en.wikipedia.org/wiki/State_machine)
