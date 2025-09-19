from dotenv import load_dotenv
import os
load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    import streamlit as st
    st.error("OPENAI_API_KEYが設定されていません。プロジェクトルートの.envファイルにAPIキーを記述してください。")

#LLMを使って（Langchain）駅間のルート検索をするWebアプリを作成するcd /Users/shotaro/THARROS Dropbox/Akizuki Shotaro/Python-Coding/stremlit-test

# 仮想環境が有効かどうかを確認し、streamlitがなければエラー表示
try:
    import streamlit as st
except ImportError:
    print("streamlitがインストールされていません。仮想環境を有効化し、'pip install streamlit' を実行してください。")
    import sys
    sys.exit(1)

st.title("鉄道ルート（輸送障害情報対応）")

st.write("##### 動作モード1: 駅間ルート検索")
st.write("出発駅と到着駅を入力することで、駅間のルートを検索できます。")
st.write("##### 動作モード2: 鉄道事故・トラブル情報")
st.write("『実行』ボタンで、首都圏の鉄道各社の事故・トラブル情報を取得します。")

selected_item = st.radio(
    "動作モードを選択してください。",
    ["駅間ルート検索", "鉄道事故・トラブル情報"]
)

st.divider()

import datetime
import pytz
if selected_item == "駅間ルート検索":
    origin = st.text_input(label="出発駅（最寄駅）を入力してください。")
    destination = st.text_input(label="到着駅（目的駅）を入力してください。")
else:
    # サーバのローカルタイムゾーンで現在時刻を取得
    now = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    st.write(f"現在時刻: {now}")
    st.info("『実行』ボタンで、首都圏の鉄道各社の事故・トラブル情報を取得します。")

if st.button("実行"):
    st.divider()

    if selected_item == "駅間ルート検索":
        metropolitan_prompt = "首都圏＝東京都、千葉県、埼玉県、茨城県、群馬県、神奈川県、山梨県、静岡県（静岡駅より西は除外）とし、それ以外の駅が入力された場合は『首都圏外の駅が含まれています』とだけ出力してください。"
        if origin and destination:
            origin = origin.strip().replace('　', '')
            destination = destination.strip().replace('　', '')
            st.write(f"出発駅: {origin}")
            st.write(f"到着駅: {destination}")
            # ここから下をAIによる一般的なルート案内に戻す
            try:
                from langchain.llms import OpenAI
                from langchain.prompts import PromptTemplate
                llm = OpenAI(openai_api_key=openai_api_key, temperature=0.3)
                prompt = PromptTemplate(
                    input_variables=["origin", "destination"],
                    template="""
                    {origin} から {destination} までの首都圏のおすすめ鉄道路線ルートを5つ、以下のフォーマットで日本語で箇条書きで提案してください。
                    ① {origin}⇒路線名⇒（必要なら乗換駅⇒路線名⇒…）⇒{destination}【所要時間XX分】
                    ※新幹線や特急は使わず、直通運転は乗換扱いしないでください。
                    ※路線名は会社名も含めて明記してください。
                    ※実在しない乗換や路線は絶対に含めないでください。
                    ※文章ではなく上記のような箇条書き形式で出力してください。
                    """
                )
                query = prompt.format(origin=origin, destination=destination)
                result = llm(query)
                # ①②③…の箇条書きで表示
                import re
                routes = [r.strip() for r in result.split("\n") if r.strip()]
                unique_routes = []
                seen = set()
                for route in routes:
                    route = re.sub(r'^[①-⑤1-5]+[.．、\s]*', '', route)
                    if route not in seen:
                        unique_routes.append(route)
                        seen.add(route)
                    if len(unique_routes) == 5:
                        break
                for idx, route in enumerate(unique_routes, 1):
                    st.write(f"{chr(9311+idx)} {route}")
            except Exception as e:
                st.error(f"ルート検索中にエラーが発生しました: {e}")
        else:
            st.error("出発駅と到着駅をどちらも入力してください。")
    else:
        # 現在時刻の首都圏鉄道各社の事故・トラブル情報をAIで取得
        try:
            from langchain.llms import OpenAI
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            prompt = f"""{now}時点での首都圏(東京都、千葉県、埼玉県、茨城県、群馬県、神奈川県、山梨県、静岡県(静岡駅より西は除外))の鉄道各社の事故・トラブル情報を、実行時点で公表されているものだけ、会社名・路線名・時刻を冒頭に含めて簡潔に日本語で箇条書きでまとめてください。情報がなければ「現在、首都圏の鉄道各社で大きな事故・トラブル情報はありません」とだけ出力してください。\n\n【出力例】\n・JR東日本 山手線 12:34 運転見合わせ(新宿〜池袋間で人身事故)\n・東京メトロ 東西線 13:10 遅延(信号トラブル)\n・…"""
            llm = OpenAI(openai_api_key=openai_api_key, temperature=0.2)
            result = llm(prompt)
            import re
            lines = [l.strip() for l in result.split("\n") if l.strip()]
            # 情報がない場合の判定と表示
            info_found = False
            now_disp = datetime.datetime.now().strftime("%m月%d日 %H:%M")
            info_found = False
            import re
            # 時刻抽出用関数
            def extract_time(line):
                match = re.search(r'(\d{1,2}:\d{2})', line)
                if match:
                    return match.group(1)
                return None

            # 「（以下略）」や「（略）」を除外し、時刻付き行のみ抽出
            valid_lines = [line for line in lines if not (line.strip().startswith("（以下略") or line.strip().startswith("（略"))]
            # 「ありません」や「なし」判定
            for line in valid_lines:
                if ("ありません" in line) or ("なし" in line):
                    st.write(f"{now_disp}現在、事故・トラブルの情報はありません。")
                    info_found = True
            if not info_found:
                # (時刻, 行) のリストを作成し、時刻の新しい順で表示
                time_line_pairs = []
                for line in valid_lines:
                    t = extract_time(line)
                    if t:
                        time_line_pairs.append((t, line))
                time_line_pairs.sort(reverse=True, key=lambda x: x[0])
                for _, line in time_line_pairs:
                    st.write(line)
        except Exception as e:
            st.error(f"障害情報取得中にエラーが発生しました: {e}")
