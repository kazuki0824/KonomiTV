
import { IMutedCommentKeywords } from '@/interface';
import APIClient from '@/services/APIClient';


/**
 * サーバーに保存されるクライアント設定を表すインターフェース
 * サーバー側の app.schemas.ClientSettings と
 * client/src/store/SettingsStore.ts 内の sync_settings_keys で定義されているものと同じ
 */
export interface IClientSettings {
    pinned_channel_ids: string[];
    // showed_panel_last_time: 同期無効
    // selected_twitter_account_id: 同期無効
    saved_twitter_hashtags: string[];
    // tv_streaming_quality: 同期無効
    // tv_data_saver_mode: 同期無効
    // tv_low_latency_mode: 同期無効
    tv_show_superimpose: boolean;
    panel_display_state: 'RestorePreviousState' | 'AlwaysDisplay' | 'AlwaysFold';
    tv_panel_active_tab: 'Program' | 'Channel' | 'Comment' | 'Twitter';
    caption_font: string;
    always_border_caption_text: boolean;
    specify_caption_background_color: boolean;
    caption_background_color: string;
    // capture_copy_to_clipboard: 同期無効
    capture_save_mode: 'Browser' | 'UploadServer' | 'Both';
    capture_caption_mode: 'VideoOnly' | 'CompositingCaption' | 'Both';
    // sync_settings: 同期無効
    comment_speed_rate: number;
    comment_font_size: number;
    // comment_delay_time: 同期無効
    close_comment_form_after_sending: boolean;
    muted_comment_keywords: IMutedCommentKeywords[];
    muted_niconico_user_ids: string[];
    mute_vulgar_comments: boolean;
    mute_abusive_discriminatory_prejudiced_comments: boolean;
    mute_big_size_comments: boolean;
    mute_fixed_comments: boolean;
    mute_colored_comments: boolean;
    mute_consecutive_same_characters_comments: boolean;
    fold_panel_after_sending_tweet: boolean;
    reset_hashtag_when_program_switches: boolean;
    auto_add_watching_channel_hashtag: boolean;
    twitter_active_tab: 'Search' | 'Timeline' | 'Capture';
    tweet_hashtag_position: 'Prepend' | 'Append' | 'PrependWithLineBreak' | 'AppendWithLineBreak';
    tweet_capture_watermark_position: 'None' | 'TopLeft' | 'TopRight' | 'BottomLeft' | 'BottomRight';
}


class Settings {

    /**
     * クライアント設定を取得する
     * @return クライアント設定 (取得に失敗した場合は null)
     */
    static async fetchClientSettings(): Promise<IClientSettings | null> {

        // API リクエストを実行
        const response = await APIClient.get<IClientSettings>('/settings/client');

        // エラー処理 (基本起こらないはず & 実行できなくても後続の処理に影響しないため何もしない)
        if ('is_error' in response) {
            return null;
        }

        return response.data;
    }


    /**
     * クライアント設定を更新する
     * @param settings クライアント設定
     */
    static async updateClientSettings(settings: IClientSettings): Promise<void> {

        // API リクエストを実行
        // 正常時は 204 No Content が返るし、エラーは基本起こらないはずなので何もしない
        await APIClient.put<IClientSettings>('/settings/client', settings);
    }
}

export default Settings;
