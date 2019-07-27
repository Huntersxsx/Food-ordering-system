from rasa_core_sdk import Action
from rasa_core_sdk.events import SlotSet
import collections
from rasa_core.agent import Agent

FoodList = ['薯条','汉堡','可乐','甜筒','爆米花','鸡翅','奶茶','巨无霸','套餐 A','套餐 B','套餐 C']

def food_price(value):
    Price = {'薯条': 7, '汉堡': 15, '可乐': 6, '甜筒': 8, '爆米花': 10, '鸡翅': 8, '奶茶': 12, '巨无霸': 20, '套餐 A': 35, '套餐 B': 36, '套餐 C': 38}
    return Price[value]


def get_all_slot_message(tracker):
    slot_name_list = []
    slot_value_list = []
    for events in tracker.events:
        if events['event'] == 'slot':
            slot_name_list.append(events['name'])
            slot_value_list.append(events['value'])
    return slot_name_list, slot_value_list


def fill_slot(tracker, dispatcher):
    entities = tracker.latest_message.get('entities')
    food_list = []
    num_list = []
    for i in range(len(entities)):
        if entities[i].get("entity") == "food":
            food_list.append(entities[i].get("value"))
        elif entities[i].get("extractor") == "ner_duckling_http":
            if entities[i].get("value") < 0:
                dispatcher.utter_message("请输入正确的食品数目!")
                food_list = []
                num_list = []
                break
            else:
                num_list.append(entities[i].get("value"))

    return food_list, num_list


def total_price_back(dict):
    price = dict['总计']
    del dict['总计']
    dict['总计'] = price
    return dict


class ActionGreet(Action):
    def name(self):
        return 'action_greet'

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message("您好!")
        return [SlotSet('fastfood', []), SlotSet('foodnumber', []), SlotSet('price', 0)]


class ActionMenu(Action):
    def name(self):
        return 'action_show_menu'

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message("薯条: 7元")
        dispatcher.utter_message("汉堡: 15元")
        dispatcher.utter_message("甜筒: 8元")
        dispatcher.utter_message("爆米花: 10元")
        dispatcher.utter_message("鸡翅: 8元")
        dispatcher.utter_message("奶茶: 12元")
        dispatcher.utter_message("巨无霸: 20元")
        dispatcher.utter_message("可乐: 6元")
        dispatcher.utter_message("套餐A: 35元")
        dispatcher.utter_message("套餐B: 36元")
        dispatcher.utter_message("套餐C: 38元")
        dispatcher.utter_message("您好，这是我们的菜单，请问您需要什么呢？")
        return []

class ActionSlotFilling(Action):
    def name(self):
        return 'action_slot_filling'

    def run(self, dispatcher, tracker, domain):
        entities = tracker.latest_message.get('entities')
        #dispatcher.utter_message("entities:{}".format(entities))
        food_list, num_list = fill_slot(tracker, dispatcher)
        if len(food_list) != len(num_list):
            dispatcher.utter_message("抱歉，您输入的食物种类和数目不对应，请重新输入")
            food_list = []
            num_list = []
        for x in food_list:
            if x not in FoodList:
                dispatcher.utter_message("抱歉，菜单中没有{}，请您重新点餐".format(x))
                food_list = []
                num_list = []
                break
        food_before = tracker.get_slot('fastfood')
        number_before = tracker.get_slot('foodnumber')
        if food_before is None:
            food_before = []
        if number_before is None:
            number_before = []
        L = []
        for i in range(len(food_list)):
            if food_list[i] in food_before:
                idx = food_before.index(food_list[i])
                number_before[idx] += num_list[i]
                L.append(i)
        cnt = 0
        for i in range(len(L)):
            food_list.remove(food_list[L[i] + cnt])
            num_list.remove(num_list[L[i] + cnt])
            cnt -= 1
        return [SlotSet('fastfood', food_before + food_list), SlotSet('foodnumber', number_before + num_list)]


class ActionAnswer(Action):
    def name(self):
        return 'action_answer'

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message.get('intent').get('name')
        food_list, num_list = fill_slot(tracker, dispatcher)
        if len(food_list) != len(num_list):
            return []
        for x in food_list:
            if x not in FoodList:
                return []
        #dispatcher.utter_message("intent:{}".format(intent))
        if intent is None:
            intent = 'others'
        if intent == 'kind_answer':
            dispatcher.utter_message("好的，请问您还需要什么吗？")
        elif intent == 'deny':
            dispatcher.utter_message("好的，请稍等。")
        elif intent == 'other':
            dispatcher.utter_message("不好意思，上班时间不能和您闲聊，请问可以再说一遍您的需求吗？")
        elif (intent == 'cancel') or (intent == 'modify_food') or (intent == 'modify_num'):
            dispatcher.utter_message("请问您还需要什么吗？")
        elif intent == 'urge_order':
            dispatcher.utter_message("好的，我们会尽快处理您的订单，请问您还有什么需求吗？")
        else:
            dispatcher.utter_message("不好意思，我没能听懂您的意思，请问可以再说一遍您的需求吗？")
        return []


class ActionCalMoney(Action):
    def name(self):
        return 'action_cal_money'

    def run(self, dispatcher, tracker, domain):
        entities = tracker.latest_message.get('entities')
        price_list = []
        num_list = []
        '''
        slot_name_list, slot_value_list = get_all_slot_message(tracker)
        for i in range(len(slot_name_list)):
            dispatcher.utter_message("slot:{}".format(slot_name_list[i]))
            dispatcher.utter_message("slot:{}".format(slot_value_list[i]))
        '''
        food_list, num_list = fill_slot(tracker, dispatcher)
        for x in food_list:
            if x not in FoodList:
                bill_list = [0]
                price_slot = tracker.get_slot("price")
                if price_slot is None:
                    price_slot = 0
                before_bill = int(price_slot)
                bill = sum(bill_list) + before_bill
                return [SlotSet('price', bill)]
        if len(food_list) != len(num_list):
            bill_list = [0]
        else:
            for i in range(len(entities)):
                if entities[i].get("entity") == "food":
                    value01 = entities[i].get("value")
                    price_tmp = food_price(value01)
                    price_list.append(price_tmp)
                elif entities[i].get("extractor") == "ner_duckling_http":
                    value02 = entities[i].get("value")
                    num_tmp = int(value02)
                    if num_tmp < 0:
                        price_slot = tracker.get_slot("price")
                        if price_slot is None:
                            price_slot = 0
                        before_bill = int(price_slot)
                        return [SlotSet('price', before_bill)]
                    else:
                        num_list.append(num_tmp)
            bill_list = [price_list[i] * num_list[i] for i in range(len(price_list))]

        price_slot = tracker.get_slot("price")
        if price_slot is None:
            price_slot = 0
        before_bill = int(price_slot)
        bill = sum(bill_list) + before_bill

        return [SlotSet('price', bill)]


class ActionCancel(Action):
    def name(self):
        return 'action_cancel'

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message.get('intent').get('name')
        if intent == 'cancel':
            entities = tracker.latest_message.get('entities')
            food_before = tracker.get_slot('fastfood')
            number_before = tracker.get_slot('foodnumber')
            price_slot = tracker.get_slot("price")
            if price_slot is None:
                price_slot = 0
            before_bill = int(price_slot)
            for i in range(len(entities)):
                if entities[i].get("entity") == "food":
                    value = entities[i].get("value")
                    if value in food_before:
                        idx = food_before.index(value)
                        bill = -1 * food_price(value) * int(number_before[idx])
                        before_bill = bill + before_bill
                        del food_before[idx]
                        del number_before[idx]
                        dispatcher.utter_message("您好，已经成功帮您取消{}的订单".format(value))
                        dispatcher.utter_message("请问您还有什么需求呢？")
                    else:
                        dispatcher.utter_message("不好意思，您没有点{}".format(value))

        return [SlotSet('fastfood', food_before), SlotSet('foodnumber', number_before), SlotSet('price', before_bill)]


#加 也等同于订餐
class ActionChangeNum(Action):
    def name(self):
        return 'action_change_num'

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message.get('intent').get('name')
        if intent == 'modify_num':
            entities = tracker.latest_message.get('entities')
            food_before = tracker.get_slot('fastfood')
            number_before = tracker.get_slot('foodnumber')
            price_slot = tracker.get_slot("price")
            if price_slot is None:
                price_slot = 0
            before_bill = int(price_slot)
            entity_name = []
            for i in range(len(entities)):
                entity_name.append(entities[i].get('entity'))
            L_food = [i for i, x in enumerate(entity_name) if x == 'food']
            L_num = [i for i, x in enumerate(entity_name) if x == 'number']
            for i in range(len(L_food)):
                idx_food = L_food[i]
                idx_num = L_num[i]
                value = entities[idx_food].get('value')
                if ("加" in tracker.latest_message.get('text')) or ("添" in tracker.latest_message.get('text')):
                    if value in food_before:
                        idx = food_before.index(value)
                        number_before[idx] += int(entities[idx_num].get('value'))
                        before_bill += food_price(value) * int(entities[idx_num].get('value'))
                        dispatcher.utter_message("已经成功帮您把{}的数量修改为{}".format(value, number_before[idx]))
                    else:
                        before_bill += int(entities[idx_num].get('value')) * food_price(value)
                        food_before = food_before + [value]
                        number_before = number_before + [entities[idx_num].get('value')]
                        dispatcher.utter_message("已经成功帮您把{}的数量修改为{}".format(value, entities[idx_num].get('value')))
                        #return [SlotSet('fastfood', food_before + [value]), SlotSet('foodnumber', number_before + [entities[idx_num].get('value')]), SlotSet('price', bill)]
                elif ("减" in tracker.latest_message.get('text')) or ("去掉" in tracker.latest_message.get('text')) or ("删" in tracker.latest_message.get('text')):
                    if value in food_before:
                        idx = food_before.index(value)
                        if number_before[idx] >= int(entities[idx_num].get('value')):
                            number_before[idx] -= int(entities[idx_num].get('value'))
                            before_bill -= food_price(value) * int(entities[idx_num].get('value'))
                            dispatcher.utter_message("已经成功帮您把{}的数量修改为{}".format(value, number_before[idx]))
                        else:
                            dispatcher.utter_message("不好意思，您之前点的{}的数量不足{}".format(value, int(entities[idx_num].get('value'))))
                    else:
                        dispatcher.utter_message("不好意思，您没有点{}".format(value))
                else:
                    if value in food_before:
                        idx = food_before.index(value)
                        L = [i for i, x in enumerate(entity_name) if x == 'number']
                        before_bill -= food_price(value) * int(entities[L[0]].get('value'))
                        before_bill += food_price(value) * int(entities[L[1]].get('value'))
                        number_before[idx] = int(entities[L[1]].get('value'))
                        dispatcher.utter_message("您好，已经成功帮您把{}的数量修改为{}".format(value, number_before[idx]))
                    else:
                        dispatcher.utter_message("不好意思，您没有点{}".format(value))

        return [SlotSet('fastfood', food_before), SlotSet('foodnumber', number_before), SlotSet('price', before_bill)]


class ActionChangeFood(Action):
    def name(self):
        return 'action_change_food'

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message.get('intent').get('name')
        if intent == 'modify_food':
            entities = tracker.latest_message.get('entities')
            food_before = tracker.get_slot('fastfood')
            number_before = tracker.get_slot('foodnumber')
            price_slot = tracker.get_slot("price")
            if price_slot is None:
                price_slot = 0
            before_bill = int(price_slot)
            entity_name = []
            for i in range(len(entities)):
                entity_name.append(entities[i].get('entity'))
            L_food = [i for i, x in enumerate(entity_name) if x == 'food']
            L_num = [i for i, x in enumerate(entity_name) if x == 'number']
            for i in range(len(L_food) - 1):
                if (i % 2 == 0):
                    value01 = entities[L_food[i]].get('value')
                    value02 = entities[L_food[i + 1]].get('value')
                    if value01 in food_before:
                        idx = food_before.index(value01)
                        before_bill -= food_price(value01) * int(number_before[idx])
                        food_before[idx] = value02
                        if L_num != []:
                            number_before[idx] = entities[L_num[-1]].get('value')
                        else:
                            number_before[idx] = 1
                        before_bill += food_price(value02) * int(number_before[idx])
                        dispatcher.utter_message("您好，已经成功帮您由{}更换成{}".format(value01, value02))
                    else:
                        dispatcher.utter_message("不好意思，您没有点{}".format(value01))

        return [SlotSet('fastfood', food_before), SlotSet('foodnumber', number_before), SlotSet('price', before_bill)]


class ActionTotalMoney(Action):
    def name(self):
        return 'action_total_money'

    def run(self, dispatcher, tracker, domain):
        food_before = tracker.get_slot('fastfood')
        number_before = tracker.get_slot('foodnumber')
        bill = tracker.get_slot("price")
        orderlist = tracker.get_slot('orderform')
        '''
        order_state = tracker.get_slot('order_state')
        if order_state is None:
            order_state = [{'13679226878':'unsend', '15261993101':'unsend'}]
        '''
        if orderlist is None:
            orderlist = []
        dict = collections.OrderedDict()
        dispatcher.utter_message("您好，这是您的订单:")
        for i in range(len(food_before)):
            if int(number_before[i]) > 0:
                dispatcher.utter_message("{}:{}".format(food_before[i],number_before[i]))
                dict[food_before[i]] = number_before[i]
        flag = 0
        for x in orderlist:
            for i,j in x.items():
                if i == '修改':
                    price = j + bill
                    idx = orderlist.index(x)
                    flag = 1
        if flag == 1:
            if bill > 0:
                dispatcher.utter_message("一共{}元，您需要再付{}元".format(price, bill))
            elif bill < 0:
                dispatcher.utter_message("一共{}元，稍后我们会退您{}元".format(price, -1 * bill))
            else:
                dispatcher.utter_message("一共{}元，修改后的订单金额与修改之前相同，无需另付或退款".format(price))
            dict['总计'] = price
            dict['id_num'] = orderlist[idx].get('id_num')
            orderlist[idx] = dict
        else:
            dispatcher.utter_message("一共是{}元。".format(bill))
            dict['总计'] = bill
            phone = tracker.get_slot('phone')
            if (phone is None) or (phone == ' '):
                phone = 13679226878
            dict['id_num'] = phone
            orderlist.append(dict)
        return [SlotSet('fastfood', []), SlotSet('foodnumber', []), SlotSet('price', 0), SlotSet('orderform',orderlist)]


class ActionAskOrder(Action):
    def name(self):
        return 'action_ask_order'

    def run(self, dispatcher, tracker, domain):
        phone = tracker.get_slot('phone')
        orderlist = tracker.get_slot('orderform')
        order_set = tracker.get_slot('order_set')
        user_intent = tracker.get_slot('user_intent')
        if (user_intent == 'error') and (tracker.latest_message.get('intent').get('name') == 'telephone_number'):
            return []
        if order_set is None:
            order_set = [{'13679226878': 'yet', '15261993101': 'yet'}]
        if orderlist is None:
            orderlist = []
        if (phone is None) or (phone == ' '):
            phone = ' '
            dispatcher.utter_message("不好意思，请先输入您的手机号")
            return [SlotSet('order_set', order_set)]
        elif phone == 13679226878:
            current_order = []
            for order in orderlist:
                if order.get('id_num') == phone:
                    current_order.append(order)
            if (current_order == []) and (order_set[0].get('13679226878') == 'yet'):
                current_order = [{'汉堡':1, '奶茶':1, '薯条':2, '总计':41, 'id_num':13679226878}]
                orderlist = orderlist + current_order
                order_set[0]['13679226878'] = 'already'
        elif phone == 15261993101:
            current_order = []
            for order in orderlist:
                if order.get('id_num') == phone:
                    current_order.append(order)
            if (current_order == []) and (order_set[0].get('15261993101') == 'yet'):
                current_order = [{'巨无霸': 2, '奶茶': 1, '可乐': 1, '总计': 58, 'id_num': 15261993101}]
                orderlist = orderlist + current_order
                order_set[0]['15261993101'] = 'already'
        if current_order == []:
            dispatcher.utter_message("不好意思，您还没有下单")
            dispatcher.utter_message("请问您还有什么需求呢？")
        else:
            dispatcher.utter_message("您好，这是您的所有订单:")
            count = 0
            bill = 0
            for order in current_order:
                count += 1
                dispatcher.utter_message("订单{}".format(count))
                for foodname,foodnum in order.items():
                    if (foodname != '总计') and (foodname != 'id_num'):
                        dispatcher.utter_message("{}:{}".format(foodname, foodnum))
                dispatcher.utter_message("{}:{}元".format('总计',order['总计']))
                bill += order['总计']
                dispatcher.utter_message('\n')
            dispatcher.utter_message("一共消费{}元".format(bill))
            dispatcher.utter_message("请问有什么需要帮助的吗？")

        return [SlotSet('orderform', orderlist), SlotSet('state', 'ask_order'), SlotSet('order_set', order_set)]


class ActionUrgeOrder(Action):
    def name(self):
        return 'action_urge_order'

    def run(self, dispatcher, tracker, domain):
        phone = tracker.get_slot('phone')
        user_intent = tracker.get_slot('user_intent')
        if (user_intent == 'error') and (tracker.latest_message.get('intent').get('name') == 'telephone_number'):
            return []
        if (phone is None) or (phone == ' '):
            phone = ' '
            dispatcher.utter_message("不好意思，请先输入您的手机号")
        elif phone == 13679226878:
            dispatcher.utter_message("好的，我们会尽快处理您的订单，请问您还有什么需求吗？")
        elif phone == 15261993101:
            dispatcher.utter_message("您好，您的订单已经发出，请您耐心等待")
            dispatcher.utter_message("请问您还有什么需求吗？")
        return [SlotSet('state', 'urge_order')]


class ActionModifyOrder(Action):
    def name(self):
        return 'action_modify_order'

    def run(self, dispatcher, tracker, domain):
        for event in tracker.events:
            if event['event'] == 'user':
                intent_tmp = event['parse_data']['intent']['name']
                if (intent_tmp == 'order_answer') or (intent_tmp == 'modify_order') or (intent_tmp == 'order_confirm') or (intent_tmp == 'modify_answer'):
                    intent = intent_tmp
        phone = tracker.get_slot('phone')
        state = tracker.get_slot('state')
        orderlist = tracker.get_slot('orderform')
        user_intent = tracker.get_slot('user_intent')
        if (user_intent == 'error') and (tracker.latest_message.get('intent').get('name') == 'telephone_number'):
            return []
        if orderlist is None:
            orderlist = []
        order_set = tracker.get_slot('order_set')
        if order_set is None:
            order_set = [{'13679226878': 'yet', '15261993101': 'yet'}]
        if (phone is None) or (phone == ' '):
            phone = ' '
            dispatcher.utter_message("不好意思，请先输入您的手机号")
            return [SlotSet('order_set', order_set)]
        elif phone == 13679226878:
            current_order = []
            for order in orderlist:
                if order.get('id_num') == phone:
                    current_order.append(order)
            if (current_order == []) and (order_set[0].get('13679226878') == 'yet'):
                current_order = [{'汉堡': 1, '奶茶': 1, '薯条': 2, '总计': 41, 'id_num': 13679226878}]
                orderlist = orderlist + current_order
                order_set[0]['13679226878'] = 'already'
        elif phone == 15261993101:
            current_order = []
            for order in orderlist:
                if order.get('id_num') == phone:
                    current_order.append(order)
            if (current_order == []) and (order_set[0].get('15261993101') == 'yet'):
                current_order = [{'巨无霸': 2, '奶茶': 1, '可乐': 1, '总计': 58, 'id_num': 15261993101}]
                orderlist = orderlist + current_order
                order_set[0]['15261993101'] = 'already'

        if (intent == 'modify_order'):
            if current_order == []:
                dispatcher.utter_message("不好意思，您还没有下单")
                dispatcher.utter_message("请问您还有什么需求呢？")
            else:
                dispatcher.utter_message("好的，这是您的所有订单:")
                count = 0
                for order in current_order:
                    count += 1
                    dispatcher.utter_message("订单{}".format(count))
                    for foodname, foodnum in order.items():
                        if (foodname != '总计') and (foodname != 'id_num'):
                            dispatcher.utter_message("{}:{}".format(foodname, foodnum))
                    dispatcher.utter_message("{}:{}元".format('总计', order['总计']))
                    dispatcher.utter_message('\n')
                if count > 1:
                    dispatcher.utter_message("请问您要修改哪一个订单呢？")
                elif count == 1:
                    dispatcher.utter_message("请问您是要修改这一个订单吗？")

            return [SlotSet('orderform', orderlist), SlotSet('state', 'modify_order'), SlotSet('order_set', order_set)]

        elif (intent == 'order_answer') or (intent == 'modify_answer'):
            if current_order == []:
                dispatcher.utter_message("不好意思，您还没有下单")
                dispatcher.utter_message("请问您还有什么需求呢？")
            else:
                for event in tracker.events:
                    if event['event'] == 'user':
                        if (event['parse_data']['intent']['name'] == 'order_answer') or (event['parse_data']['intent']['name'] == 'modify_answer'):
                            idx = int(event['parse_data']['entities'][-1].get('value'))
                if idx > len(current_order):
                    dispatcher.utter_message("不好意思，您的订单数量不足{}，可以重说一下您的需求吗？".format(idx))
                    return [SlotSet('orderform', orderlist), SlotSet('state', 'modify_order'), SlotSet('order_set', order_set)]
                elif (idx == 1) and (phone == 15261993101):
                    dispatcher.utter_message("不好意思，订单1已经发出，不能修改，给您带来不便，深感歉意")
                    dispatcher.utter_message("请问您还有什么需求呢？")
                    return [SlotSet('orderform', orderlist), SlotSet('state', 'modify_order'), SlotSet('order_set', order_set)]
                else:
                    dispatcher.utter_message("好的，请问您需要修改什么呢？")
                    order = current_order[idx - 1]
                    food_list = []
                    num_list = []
                    bill_tmp = order['总计']
                    id_num = order['id_num']
                    bill = 0
                    del order['总计']
                    del order['id_num']
                    for k in order.keys():
                        food_list.append(k)
                    for v in order.values():
                        num_list.append(v)
                    idx2 = orderlist.index(order)
                    orderlist[idx2] = {'修改':bill_tmp, 'id_num':id_num}
                    return [SlotSet('fastfood', food_list), SlotSet('foodnumber', num_list), SlotSet('price', bill), SlotSet('orderform', orderlist), SlotSet('state', 'modify_order'), SlotSet('order_set', order_set)]
            return [SlotSet('orderform', orderlist), SlotSet('state', 'modify_order'), SlotSet('order_set', order_set)]

        elif (intent == 'order_confirm'):
            if current_order == []:
                dispatcher.utter_message("不好意思，您还没有下单")
                dispatcher.utter_message("请问您还有什么需求呢？")
            else:
                if phone == 15261993101:
                    dispatcher.utter_message("不好意思，订单1已经发出，不能修改，给您带来不便，深感歉意")
                    dispatcher.utter_message("请问您还有什么需求呢？")
                else:
                    dispatcher.utter_message("好的，请问您需要修改什么呢？")
                    order = current_order[0]
                    food_list = []
                    num_list = []
                    bill_tmp = order['总计']
                    id_num = order['id_num']
                    bill = 0
                    del order['总计']
                    del order['id_num']
                    for k in order.keys():
                        food_list.append(k)
                    for v in order.values():
                        num_list.append(v)
                    idx2 = orderlist.index(order)
                    orderlist[idx2] = {'修改': bill_tmp, 'id_num': id_num}
                    return [SlotSet('fastfood', food_list), SlotSet('foodnumber', num_list), SlotSet('price', bill), SlotSet('orderform', orderlist), SlotSet('state', 'modify_order'), SlotSet('order_set', order_set)]
            return [SlotSet('orderform', orderlist), SlotSet('state', 'modify_order'), SlotSet('order_set', order_set)]

        return []

class ActionCancelOrder(Action):
    def name(self):
        return 'action_cancel_order'

    def run(self, dispatcher, tracker, domain):
        for event in tracker.events:
            if event['event'] == 'user':
                intent_tmp = event['parse_data']['intent']['name']
                if (intent_tmp == 'cancel_answer') or (intent_tmp == 'order_cancel') or (intent_tmp == 'order_confirm') or (intent_tmp == 'order_answer'):
                    intent = intent_tmp
        phone = tracker.get_slot('phone')
        #order_state = tracker.get_slot('order_state')
        orderlist = tracker.get_slot('orderform')
        order_set = tracker.get_slot('order_set')
        user_intent = tracker.get_slot('user_intent')
        if (user_intent == 'error') and (tracker.latest_message.get('intent').get('name') == 'telephone_number'):
            return []
        if order_set is None:
            order_set = [{'13679226878': 'yet', '15261993101': 'yet'}]
        if orderlist is None:
            orderlist = []
        if (phone is None) or (phone == ' '):
            phone = ' '
            dispatcher.utter_message("不好意思，请先输入您的手机号")
            return [SlotSet('order_set', order_set)]
        elif phone == 13679226878:
            current_order = []
            for order in orderlist:
                if order.get('id_num') == phone:
                    current_order.append(order)
            if (current_order == []) and (order_set[0].get('13679226878') == 'yet'):
                current_order = [{'汉堡': 1, '奶茶': 1, '薯条': 2, '总计': 41, 'id_num': 13679226878}]
                orderlist = orderlist + current_order
                order_set[0]['13679226878'] = 'already'
        elif phone == 15261993101:
            current_order = []
            for order in orderlist:
                if order.get('id_num') == phone:
                    current_order.append(order)
            if (current_order == []) and (order_set[0].get('15261993101') == 'yet'):
                current_order = [{'汉堡': 1, '奶茶': 1, '薯条': 2, '总计': 41, 'id_num': 15261993101}]
                orderlist = orderlist + current_order
                order_set[0]['15261993101'] = 'already'

        if (intent == 'order_cancel'):
            if current_order == []:
                dispatcher.utter_message("不好意思，您还没有下单")
                dispatcher.utter_message("请问您还有什么需求呢？")
            else:
                dispatcher.utter_message("好的，这是您的所有订单:")
                count = 0
                for order in current_order:
                    count += 1
                    dispatcher.utter_message("订单{}".format(count))
                    for foodname, foodnum in order.items():
                        if (foodname != '总计') and (foodname != 'id_num'):
                            dispatcher.utter_message("{}:{}".format(foodname, foodnum))
                    dispatcher.utter_message("{}:{}元".format('总计', order['总计']))
                    dispatcher.utter_message('\n')
                if count > 1:
                    dispatcher.utter_message("请问您要取消哪一个订单呢？")
                elif count == 1:
                    dispatcher.utter_message("请问您是要取消这一个订单吗？")

            return [SlotSet('orderform', orderlist), SlotSet('state', 'order_cancel'), SlotSet('order_set', order_set)]

        elif (intent == 'order_answer') or (intent == 'cancel_answer'):
            if current_order == []:
                dispatcher.utter_message("不好意思，您还没有下单")
                dispatcher.utter_message("请问您还有什么需求呢？")
            else:
                for event in tracker.events:
                    if event['event'] == 'user':
                        if (event['parse_data']['intent']['name'] == 'order_answer') or (event['parse_data']['intent']['name'] == 'cancel_answer'):
                            idx = int(event['parse_data']['entities'][-1].get('value'))
                if idx > len(current_order):
                    dispatcher.utter_message("不好意思，您的订单数量不足{}，可以重说一下您的需求吗？".format(idx))
                    return [SlotSet('orderform', orderlist), SlotSet('state', 'order_cancel'), SlotSet('order_set', order_set)]
                elif (idx == 1) and (phone == 15261993101):
                    dispatcher.utter_message("不好意思，订单1已经发出，不能取消，给您带来不便，深感歉意")
                    dispatcher.utter_message("请问您还有什么需求呢？")
                    return [SlotSet('orderform', orderlist), SlotSet('state', 'order_cancel'), SlotSet('order_set', order_set)]
                else:
                    order = current_order[idx - 1]
                    orderlist.remove(order)
                    dispatcher.utter_message("好的，已经帮您取消订单{}".format(idx))
                    dispatcher.utter_message("请问您还有什么需求呢？")
                    return [SlotSet('orderform', orderlist), SlotSet('state', 'order_cancel'), SlotSet('order_set', order_set)]
            return [SlotSet('orderform', orderlist), SlotSet('state', 'order_cancel'), SlotSet('order_set', order_set)]

        elif (intent == 'order_confirm'):
            if current_order == []:
                dispatcher.utter_message("不好意思，您还没有下单")
                dispatcher.utter_message("请问您还有什么需求呢？")
            else:
                if phone == 15261993101:
                    dispatcher.utter_message("不好意思，订单1已经发出，不能取消，给您带来不便，深感歉意")
                    dispatcher.utter_message("请问您还有什么需求呢？")
                    return [SlotSet('orderform', orderlist), SlotSet('state', 'order_cancel'), SlotSet('order_set', order_set)]
                else:
                    order = current_order[0]
                    orderlist.remove(order)
                    dispatcher.utter_message("好的，已经帮您取消该订单")
                    dispatcher.utter_message("请问您还有什么需求呢？")
                    return [SlotSet('orderform', orderlist), SlotSet('state', 'order_cancel'), SlotSet('order_set', order_set)]
            return [SlotSet('orderform', orderlist), SlotSet('state', 'order_cancel'), SlotSet('order_set', order_set)]

        return [SlotSet('state', 'order_cancel')]


class ActionTelephone(Action):
    def name(self):
        return 'action_check_telephone'

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message.get('intent').get('name')
        orderlist = tracker.get_slot('orderform')
        if orderlist is None:
            orderlist = []
        if (intent == 'modify_order') or (intent == 'order_answer') or (intent == 'ask_order'):
            phone_num = ' '
            dispatcher.utter_message("不好意思，请先输入您的手机号")
        elif intent == 'telephone_number':
            text = tracker.latest_message.get('text')
            import re
            pattern = re.compile('(13(7|8|9|6|5|4)|17(0|8|3|7)|18(2|3|6|7|9)|15(2|3|5|6|7|8|9))\d{8}')
            phone = pattern.search(text)
            if phone:
                entities = tracker.latest_message.get('entities')
                phone_num = entities[0].get('value')
                if (phone_num == 13679226878) or (phone_num == 15261993101):
                    dispatcher.utter_message("好的，请稍等")
                    for event in tracker.events:
                        if event['event'] == 'user':
                            intent_tmp = event['parse_data']['intent']['name']
                            if (intent_tmp == 'order_cancel') or (intent_tmp == 'cancel_answer') or (intent_tmp == 'modify_order') or (intent_tmp == 'ask_order') or (intent_tmp == 'urge_order') or (intent_tmp == 'modify_answer'):
                                user_intent = intent_tmp
                    return [SlotSet('phone', phone_num), SlotSet('user_intent', user_intent)]
                else:
                    dispatcher.utter_message("不好意思，没有查到该手机号的相关订单")
                    dispatcher.utter_message("请问您还有什么需求呢？")
                    phone_num = ' '
            else:
                phone_num = ' '
                dispatcher.utter_message("请输入正确的手机号格式")
        return [SlotSet('phone', phone_num), SlotSet('user_intent', 'error')]


class ActionDeny(Action):
    def name(self):
        return 'action_deny_order'

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message("好的，谢谢惠顾，祝您生活愉快！")
        order_set = [{'13679226878': 'yet', '15261993101': 'yet'}]
        return [SlotSet('phone', ' '), SlotSet('state', 'deny_order'), SlotSet('order_set', order_set)]


class ActionAgain(Action):
    def name(self):
        return 'action_again'
    def run(self, dispatcher, tracker, domain):
        text_list = []
        user_list = []
        bot_list = []
        for event in tracker.events:
            if (event['event'] == 'user') or (event['event'] == 'bot'):
                text_list.append(event['text'])
            if event['event'] == 'user':
                user_list.append(event['text'])
        pardon_text = user_list[-2]
        L = [i for i, x in enumerate(text_list) if x == pardon_text]
        for i in range(L[-1] + 1,len(text_list) - 1):
            bot_list.append(text_list[i])
        dispatcher.utter_message('好的，我将为您重复一遍之前的话语')
        dispatcher.utter_message('\n')
        for i in range(len(bot_list)):
            dispatcher.utter_message('{}'.format(bot_list[i]))
        return []

















        #dispatcher.utter_message("您好，一共是{}元。".format(bill))
        #dispatcher.utter_message("user_message:{}".format(user_message))
        #dispatcher.utter_message("user_intent:{}".format(user_intent))
        #dispatcher.utter_message("entities:{}".format(user_message[1]))
        #dispatcher.utter_message("length:{}".format(len(user_message)))
        #dispatcher.utter_message("entity:{}".format(user_message[1][0].get("value")))
#entities
'''
entities:[{'start': 2, 'end': 4, 'value': '1', 'entity': 'quan', 'confidence': 0.9880497969162052, 'extractor': 'ner_crf', 'processors': ['ner_synonyms']},
 {'start': 4, 'end': 6, 'value': '汉堡', 'entity': 'food', 'confidence': 0.9927043923488859, 'extractor': 'ner_crf'},
  {'start': 7, 'end': 9, 'value': '1', 'entity': 'quan', 'confidence': 0.9980485915344901, 'extractor': 'ner_crf', 'processors': ['ner_synonyms']}, 
  {'start': 9, 'end': 11, 'value': '可乐', 'entity': 'food', 'confidence': 0.9982513564658912, 'extractor': 'ner_crf'}, 
  {'start': 12, 'end': 14, 'value': '1', 'entity': 'quan', 'confidence': 0.9972201526590433, 'extractor': 'ner_crf', 'processors': ['ner_synonyms']}, 
  {'start': 14, 'end': 16, 'value': '鸡翅', 'entity': 'food', 'confidence': 0.9978083810312598, 'extractor': 'ner_crf'}]
'''









