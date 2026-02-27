import random
import pygame
import sys
from pygame.locals import *
import time
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools # type: ignore

SCOPES = "https://www.googleapis.com/auth/forms.responses.readonly"
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

store = file.Storage("token.json")
creds = None
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets("client_secrets.json", SCOPES)
    creds = tools.run_flow(flow, store)

service = discovery.build(
    "forms",
    "v1",
    http=creds.authorize(Http()),
    discoveryServiceUrl=DISCOVERY_DOC,
    static_discovery=False,
)

form_id = "1QlJGJdqpK69tRjxamH9YfnadypvAQW3bsIdJuBiCce4"

# すでに表示した解答を追跡
displayed_responses = set()
# 読み込む回答を格納する配列の定義
loaded_comments = []
# コメントに割り当てる変数
commentNumber = 0
# NGワードのリスト
NGwords = []
with open("NGwords.txt", mode="r", encoding="utf-8") as f:
    for line in f.readlines():
        line = line.replace("\n", "")

        if line[0] == "#":
            continue
        NGwords.append(line)

def fetch_new_responses():
    result = service.forms().responses().list(formId=form_id).execute()
    responses = result.get("responses", [])

    for response in responses:
        response_id = response["responseId"]
        if response_id not in displayed_responses:
            answers = response.get("answers", {})
            for question_id, answer_data in answers.items():
                text_answers = answer_data.get("textAnswers", {}).get("answers", [])
                for answer in text_answers:
                    loaded_comments.append(answer.get("value")) #コメントを配列に追加
                    commentNumber = len(loaded_comments) # コメントに順番に数字を割り当て
            displayed_responses.add(response_id)

# 画面サイズ 1920x1080
SCREEN_SIZE = (1920, 1080)
FONTPATH = "NotoSansJP-Bold.ttf"
displaying_comments = []
last_fetch_time = 0

def main():
    global last_fetch_time
    global commentNumber
    
    # Pygameの初期化
    pygame.init()

    # 画面設定（★起動時はフルスクリーン表示、解除時は指定したサイズ1920x1080になる）
    screen = pygame.display.set_mode(
        SCREEN_SIZE, FULLSCREEN)

    # タイトルバーに表示する文字
    pygame.display.set_caption("Test")
    
    # FPSの設定
    clock = pygame.time.Clock()
    fps_limit = 60

    font = pygame.font.Font(FONTPATH, 60) # フォントの設定
    while True:
        # 画面を黒色(#000000)に塗りつぶし
        screen.fill((0, 0, 0))
        
        # 座標やスピードの初期設定
        startX = 1920
        startY = random.randint(0, 600)
        
        
        displayed_comments = []
        
        # フレームレートを60に設定
        clock.tick(fps_limit)
        
        current_time = pygame.time.get_ticks()
        if current_time - last_fetch_time > 7000:
            fetch_new_responses() # コメントの読み込み
            last_fetch_time = current_time
        
        # 描画するコメントを配列に格納
        if loaded_comments:
            allowDisplay = True

            for word in NGwords:
                if word.lower() in loaded_comments[commentNumber - 1].lower():
                    allowDisplay = False
                    print(f"NGword: {word} is in {loaded_comments[commentNumber - 1]}")
                    break

            if len(loaded_comments[commentNumber - 1]) > 15:
                allowDisplay = False
                print(f"NGword: {loaded_comments[commentNumber - 1]} is too long")

            try:
                text = font.render(
                    loaded_comments[commentNumber - 1],
                    True,
                    (255, 255, 255)
                )
                speed = 4 + len(loaded_comments[commentNumber - 1]) * 0.8
                if not displaying_comments or loaded_comments[commentNumber - 1] != displaying_comments[len(displaying_comments) - 1]["comment"] and allowDisplay:
                    displaying_comments.append(
                        {"text": text, "posX": startX, "posY": startY, "speed": speed, "comment": loaded_comments[commentNumber - 1]}
                    )
            except UnicodeError:
                pass
        
        i = 0
        while len(displaying_comments) > i:
            displaying_comments[i]["posX"] -= displaying_comments[i]["speed"]
        
            if displaying_comments[i]["posX"]  + 10000 < 0:
                displaying_comments.pop(i)
                continue
            
            screen.blit(displaying_comments[i]["text"],[
                displaying_comments[i]["posX"],
                displaying_comments[i]["posY"]])
        
            i += 1
        
        # 画面を更新
        pygame.display.update()
        
        # イベント処理
        for event in pygame.event.get():
            # 閉じるボタンが押されたら終了
            if event.type == QUIT:  
                pygame.quit()       # Pygameの終了(画面閉じられる)
                sys.exit()

            # キーイベント（何かキーが押されたときに発生するイベント処理）
            if event.type == KEYDOWN:
                # ESCキーが押されたら終了
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

if __name__ == "__main__":
    main()