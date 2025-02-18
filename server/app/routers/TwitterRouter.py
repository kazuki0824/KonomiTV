
import asyncio
import tweepy
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from fastapi import Request
from fastapi import status
from fastapi import UploadFile
from typing import Any, cast, Coroutine

from app import schemas
from app.models import TwitterAccount
from app.models import User
from app.utils import Logging
from app.utils import OAuthCallbackResponse


# ルーター
router = APIRouter(
    tags = ['Twitter'],
    prefix = '/api/twitter',
)


# Twitter API のエラーメッセージの定義
## 実際に返ってくる可能性があるものだけ
## ref: https://developer.twitter.com/ja/docs/basics/response-codes
error_messages = {
    32:  'アカウントの認証に失敗しました。',
    63:  'アカウントが凍結またはロックされています。',
    64:  'アカウントが凍結またはロックされています。',
    88:  'API エンドポイントのレート制限を超えました。',
    89:  'アクセストークンの有効期限が切れています。',
    99:  'OAuth クレデンシャルの認証に失敗しました。',
    131: 'Twitter でサーバーエラーが発生しています。',
    135: 'アカウントの認証に失敗しました。',
    139: 'すでにいいねされています。',
    144: 'ツイートが削除されています。',
    179: 'フォローしていない非公開アカウントのツイートは表示できません。',
    185: 'ツイート数の上限に達しました。',
    186: 'ツイートが長過ぎます。',
    187: 'ツイートが重複しています。',
    226: 'ツイートが自動化されたスパムと判定されました。',
    261: 'Twitter API アプリケーションが凍結されています。',
    326: 'アカウントが一時的にロックされています。',
    327: 'すでにリツイートされています。',
    416: 'Twitter API アプリケーションが無効化されています。',
}


@router.get(
    '/auth',
    summary = 'Twitter OAuth 認証 URL 発行 API',
    response_model = schemas.ThirdpartyAuthURL,
    response_description = 'ユーザーにアプリ連携してもらうための認証 URL。',
)
async def TwitterAuthURLAPI(
    request: Request,
    current_user: User = Depends(User.getCurrentUser),
):
    """
    Twitter アカウントと連携するための認証 URL を取得する。<br>
    認証 URL をブラウザで開くとアプリ連携の許可を求められ、ユーザーが許可すると /api/twitter/callback に戻ってくる。

    JWT エンコードされたアクセストークンがリクエストの Authorization: Bearer に設定されていないとアクセスできない。<br>
    """

    # クライアント (フロントエンド) の URL を Origin ヘッダーから取得
    ## Origin ヘッダーがリクエストに含まれていない場合はこの API サーバーの URL を使う
    client_url = cast(str, request.headers.get('Origin', f'https://{request.url.netloc}')).rstrip('/') + '/'

    # コールバック URL を設定
    ## Twitter API の OAuth 連携では、事前にコールバック先の URL をデベロッパーダッシュボードから設定しておく必要がある
    ## 一方 KonomiTV サーバーの URL はまちまちなので、コールバック先の URL を一旦 https://app.konomi.tv/api/redirect/twitter に集約する
    ## この API は、リクエストを "server" パラメーターで指定された KonomiTV サーバーの TwitterAuthCallbackAPI にリダイレクトする
    ## 最後に KonomiTV サーバーがリダイレクトを受け取ることで、コールバック対象の URL が定まらなくても OAuth 連携ができるようになる
    ## "client" パラメーターはスマホ・タブレットでの TwitterAuthCallbackAPI のリダイレクト先 URL として使われる
    ## Twitter だけ他のサービスと違い OAuth 1.0a なので、フローがかなり異なる
    ## ref: https://github.com/tsukumijima/KonomiTV-API
    callback_url = f'https://app.konomi.tv/api/redirect/twitter?server=https://{request.url.netloc}/&client={client_url}'

    # OAuth1UserHandler を初期化し、認証 URL を取得
    ## signin_with_twitter を True に設定すると、oauth/authenticate の認証 URL が生成される
    ## oauth/authorize と異なり、すでにアプリ連携している場合は再承認することなくコールバック URL にリダイレクトされる
    ## ref: https://developer.twitter.com/ja/docs/authentication/api-reference/authenticate
    try:
        from app.app import consumer_key, consumer_secret
        oauth_handler = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, callback=callback_url)
        authorization_url = await asyncio.to_thread(oauth_handler.get_authorization_url, signin_with_twitter=False)  # 同期関数なのでスレッド上で実行
    except tweepy.TweepyException:
        Logging.error('[TwitterRouter][TwitterAuthURLAPI] Failed to get Twitter authorization URL')
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'Failed to get Twitter authorization URL',
        )

    # 認証 URL に force_login=true をつけることで、Twitter にログイン中でも強制的にログインフォームを表示できる
    # KonomiTV アカウントに複数の Twitter アカウントを登録する場合、毎回一旦 Twitter を開いてアカウントを切り替えるのは（特にスマホの場合）かなり面倒
    authorization_url = f'{authorization_url}&force_login=true'

    # 仮で TwitterAccount のレコードを作成
    ## 戻ってきたときに oauth_token がどのユーザーに紐づいているのかを判断するため
    ## TwitterAuthCallbackAPI は仕組み上認証をかけられないので、勝手に任意のアカウントを紐付けられないためにはこうせざるを得ない
    twitter_account = TwitterAccount()
    twitter_account.user = current_user
    twitter_account.name = 'Temporary'
    twitter_account.screen_name = 'Temporary'
    twitter_account.icon_url = 'Temporary'
    twitter_account.access_token = oauth_handler.request_token['oauth_token']  # 暫定的に oauth_token を格納 (認証 URL の ?oauth_token= と同じ値)
    twitter_account.access_token_secret = oauth_handler.request_token['oauth_token_secret']  # 暫定的に oauth_token_secret を格納
    await twitter_account.save()

    return {'authorization_url': authorization_url}


@router.get(
    '/callback',
    summary = 'Twitter OAuth コールバック API',
    response_class = OAuthCallbackResponse,
    response_description = 'ユーザーアカウントに Twitter アカウントのアクセストークン・アクセストークンシークレットが登録できたことを示す。',
)
async def TwitterAuthCallbackAPI(
    client: str = Query(..., description='OAuth 連携元の KonomiTV クライアントの URL 。'),
    oauth_token: str | None = Query(None, description='コールバック元から渡された oauth_token。OAuth 認証が成功したときのみセットされる。'),
    oauth_verifier: str | None = Query(None, description='コールバック元から渡された oauth_verifier。OAuth 認証が成功したときのみセットされる。'),
    denied: str | None = Query(None, description='このパラメーターがセットされているとき、OAuth 認証がユーザーによって拒否されたことを示す。'),
):
    """
    Twitter の OAuth 認証のコールバックを受け取り、ログイン中のユーザーアカウントと Twitter アカウントを紐づける。
    """

    # スマホ・タブレット向けのリダイレクト先 URL を生成
    redirect_url = f'{client.rstrip("/")}/settings/twitter'

    # "denied" パラメーターがセットされている
    # OAuth 認証がユーザーによって拒否されたことを示しているので、401 エラーにする
    if denied is not None:

        # 認証が失敗したので、TwitterAuthURLAPI で作成されたレコードを削除
        ## "denied" パラメーターの値は oauth_token と同一
        twitter_account = await TwitterAccount.filter(access_token=denied).get_or_none()
        if twitter_account:
            await twitter_account.delete()

        # 401 エラーを送出
        Logging.error('[TwitterRouter][TwitterAuthCallbackAPI] Authorization was denied by user')
        return OAuthCallbackResponse(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Authorization was denied by user',
            redirect_to = redirect_url,
        )

    # なぜか oauth_token も oauth_verifier もない
    if oauth_token is None or oauth_verifier is None:
        Logging.error('[TwitterRouter][TwitterAuthCallbackAPI] oauth_token or oauth_verifier does not exist')
        return OAuthCallbackResponse(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'oauth_token or oauth_verifier does not exist',
            redirect_to = redirect_url,
        )

    # oauth_token に紐づく Twitter アカウントを取得
    twitter_account = await TwitterAccount.filter(access_token=oauth_token).get_or_none()
    if not twitter_account:
        Logging.error(f'[TwitterRouter][TwitterAuthCallbackAPI] TwitterAccount associated with oauth_token does not exist [oauth_token: {oauth_token}]')
        return OAuthCallbackResponse(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'TwitterAccount associated with oauth_token does not exist',
            redirect_to = redirect_url,
        )

    # OAuth1UserHandler を初期化
    ## ref: https://docs.tweepy.org/en/latest/authentication.html#legged-oauth
    from app.app import consumer_key, consumer_secret
    oauth_handler = tweepy.OAuth1UserHandler(consumer_key, consumer_secret)
    oauth_handler.request_token = {
        'oauth_token': twitter_account.access_token,
        'oauth_token_secret': twitter_account.access_token_secret,
    }

    # アクセストークン・アクセストークンシークレットを取得し、仮の oauth_token, oauth_token_secret と置き換える
    ## 同期関数なのでスレッド上で実行
    try:
        twitter_account.access_token, twitter_account.access_token_secret = await asyncio.to_thread(oauth_handler.get_access_token, oauth_verifier)
    except tweepy.TweepyException:
        Logging.error('[TwitterRouter][TwitterAuthCallbackAPI] Failed to get access token')
        return OAuthCallbackResponse(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'Failed to get access token',
            redirect_to = redirect_url,
        )

    # tweepy を初期化
    api = tweepy.API(tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret, twitter_account.access_token, twitter_account.access_token_secret,
    ))

    # アカウント情報を更新
    try:
        verify_credentials = await asyncio.to_thread(api.verify_credentials)
    except tweepy.TweepyException:
        Logging.error('[TwitterRouter][TwitterAuthCallbackAPI] Failed to get user information')
        return OAuthCallbackResponse(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'Failed to get user information',
            redirect_to = redirect_url,
        )
    # アカウント名
    twitter_account.name = verify_credentials.name
    # スクリーンネーム
    twitter_account.screen_name = verify_credentials.screen_name
    # アイコン URL
    ## (ランダムな文字列)_normal.jpg だと画像サイズが小さいので、(ランダムな文字列).jpg に置換
    twitter_account.icon_url = verify_credentials.profile_image_url_https.replace('_normal', '')

    # 同じスクリーンネームを持つアカウントが重複している場合、古い方のレコードのデータを更新する
    # すでに作成されている新しいレコード（まだ save() していないので仮の情報しか入っていない）は削除される
    twitter_account_existing = await TwitterAccount.filter(
        user_id = cast(Any, twitter_account).user_id,
        screen_name = twitter_account.screen_name,
    ).get_or_none()
    if twitter_account_existing is not None:
        twitter_account_existing.name = twitter_account.name  # アカウント名
        twitter_account_existing.icon_url = twitter_account.icon_url  # アイコン URL
        twitter_account_existing.access_token = twitter_account.access_token  # アクセストークン
        twitter_account_existing.access_token_secret = twitter_account.access_token_secret  # アクセストークンシークレット
        await twitter_account_existing.save()
        await twitter_account.delete()

        return OAuthCallbackResponse(
            status_code = status.HTTP_200_OK,
            detail = 'Success',
            redirect_to = redirect_url,
        )

    # アクセストークンとアカウント情報を保存
    await twitter_account.save()

    # OAuth 連携が正常に完了したことを伝える
    return OAuthCallbackResponse(
        status_code = status.HTTP_200_OK,
        detail = 'Success',
        redirect_to = redirect_url,
    )


@router.delete(
    '/accounts/{screen_name}',
    summary = 'Twitter アカウント連携解除 API',
    status_code = status.HTTP_204_NO_CONTENT,
)
async def TwitterAccountDeleteAPI(
    screen_name: str = Path(..., description='連携を解除する Twitter アカウントのスクリーンネーム。'),
    current_user: User = Depends(User.getCurrentUser),
):
    """
    指定された Twitter アカウントの連携を解除する。<br>
    JWT エンコードされたアクセストークンがリクエストの Authorization: Bearer に設定されていないとアクセスできない。
    """

    # 指定されたスクリーンネームに紐づく Twitter アカウントを取得
    # 自分が所有していない Twitter アカウントでツイートできないよう、ログイン中のユーザーに限って絞り込む
    twitter_account = await TwitterAccount.filter(user_id=current_user.id, screen_name=screen_name).get_or_none()

    # 指定された Twitter アカウントがユーザーアカウントに紐付けられていない or 登録されていない
    ## 実際に Twitter にそのスクリーンネームのアカウントが登録されているかとは無関係
    if not twitter_account:
        Logging.error(f'[TwitterRouter][TwitterAccountDeleteAPI] TwitterAccount associated with screen_name does not exist [screen_name: {screen_name}]')
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'TwitterAccount associated with screen_name does not exist',
        )

    # 指定された Twitter アカウントのレコードを削除
    ## アクセストークンなどが保持されたレコードを削除することで連携解除とする
    await twitter_account.delete()


@router.post(
    '/accounts/{screen_name}/tweets',
    summary = 'ツイート送信 API',
    response_description = 'ツイートの送信結果。',
    response_model = schemas.TweetResult,
)
async def TwitterTweetAPI(
    screen_name: str = Path(..., description='ツイートする Twitter アカウントのスクリーンネーム。'),
    tweet: str = Form('', description='ツイートの本文（基本的には140文字まで）。'),
    images: list[UploadFile] | None = File(None, description='ツイートに添付する画像（4枚まで）。'),
    current_user: User = Depends(User.getCurrentUser),
):
    """
    Twitter にツイートを送信する。<br>
    ツイートには screen_name で指定したスクリーンネームに紐づく Twitter アカウントが利用される。

    JWT エンコードされたアクセストークンがリクエストの Authorization: Bearer に設定されていないとアクセスできない。
    """

    # 指定されたスクリーンネームに紐づく Twitter アカウントを取得
    # 自分が所有していない Twitter アカウントでツイートできないよう、ログイン中のユーザーに限って絞り込む
    twitter_account = await TwitterAccount.filter(user_id=current_user.id, screen_name=screen_name).get_or_none()

    # 指定された Twitter アカウントがユーザーアカウントに紐付けられていない or 登録されていない
    ## 実際に Twitter にそのスクリーンネームのアカウントが登録されているかとは無関係
    if not twitter_account:
        Logging.error(f'[TwitterRouter][TwitterTweetAPI] TwitterAccount associated with screen_name does not exist [screen_name: {screen_name}]')
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'TwitterAccount associated with screen_name does not exist',
        )

    # 画像が4枚を超えている
    if images is None:
        images = []
    if len(images) > 4:
        Logging.error(f'[TwitterRouter][TwitterTweetAPI] Can tweet up to 4 images [image length: {len(images)}]')
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = 'Can tweet up to 4 images',
        )

    # tweepy を初期化
    from app.app import consumer_key, consumer_secret
    api = tweepy.API(tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret, twitter_account.access_token, twitter_account.access_token_secret,
    ))

    # アップロードした画像の media_id のリスト
    media_ids: list[str] = []

    try:

        # 画像をアップロードするタスク
        image_upload_task: list[Coroutine] = []
        for image in images:
            image_upload_task.append(asyncio.to_thread(api.media_upload, filename=image.filename, file=image.file))

        # 画像を Twitter にアップロード
        ## asyncio.gather() で同時にアップロードし、ツイートをより早く送信できるように
        ## ref: https://developer.twitter.com/ja/docs/media/upload-media/api-reference/post-media-upload-init
        for image_upload_result in await asyncio.gather(*image_upload_task):
            media_ids.append(image_upload_result.media_id)

        # ツイートを送信
        result = await asyncio.to_thread(api.update_status, tweet, media_ids=media_ids)

    # 送信失敗
    except tweepy.HTTPException as ex:

        # API のエラーコードがない
        if len(ex.api_codes) == 0:
            return {
                'is_success': False,
                'detail': f'Message: {ex.api_errors[0]} (HTTP Error {ex.response.status_code})',
            }

        # エラーメッセージ
        # 定義されていないエラーコードの時は Twitter API から返ってきたエラーをそのまま返す
        return {
            'is_success': False,
            'detail': error_messages.get(ex.api_codes[0], f'Code: {ex.api_codes[0]}, Message: {ex.api_messages[0]}'),
        }

    return {
        'is_success': True,
        'tweet_url': f'https://twitter.com/{result.user.screen_name}/status/{result.id}',
        'detail': 'ツイートを送信しました。',
    }


@router.put(
    '/accounts/{screen_name}/tweets/{tweet_id}/retweet',
    summary = 'リツイート実行 API',
)
async def TwitterRetweetAPI(
    current_user: User = Depends(User.getCurrentUser),
):
    """
    API 実装中…（モックアップ）
    """


@router.delete(
    '/accounts/{screen_name}/tweets/{tweet_id}/retweet',
    summary = 'リツイート取り消し API',
)
async def TwitterRetweetCancelAPI(
    current_user: User = Depends(User.getCurrentUser),
):
    """
    API 実装中…（モックアップ）
    """


@router.put(
    '/accounts/{screen_name}/tweets/{tweet_id}/favorite',
    summary = 'いいね実行 API',
)
async def TwitterFavoriteAPI(
    current_user: User = Depends(User.getCurrentUser),
):
    """
    API 実装中…（モックアップ）
    """


@router.delete(
    '/accounts/{screen_name}/tweets/{tweet_id}/favorite',
    summary = 'いいね取り消し API',
)
async def TwitterFavoriteCancelAPI(
    current_user: User = Depends(User.getCurrentUser),
):
    """
    API 実装中…（モックアップ）
    """


@router.get(
    '/accounts/{screen_name}/timeline',
    summary = 'ホームタイムライン取得 API',
)
async def TwitterTimelineAPI(
    current_user: User = Depends(User.getCurrentUser),
):
    """
    API 実装中…（モックアップ）
    """


@router.get(
    '/search',
    summary = 'ツイート検索 API',
)
async def TwitterSearchAPI(
    current_user: User = Depends(User.getCurrentUser),
):
    """
    API 実装中…（モックアップ）
    """
