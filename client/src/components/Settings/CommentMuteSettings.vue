<template>
    <v-dialog max-width="740" transition="slide-y-transition" v-model="comment_mute_settings_modal">
        <v-card class="comment-mute-settings">
            <v-card-title class="px-5 pt-5 pb-3 d-flex align-center font-weight-bold" style="height: 60px;">
                <Icon icon="heroicons-solid:filter" height="26px" />
                <span class="ml-3">コメントのミュート設定</span>
                <v-spacer></v-spacer>
                <div v-ripple class="d-flex align-center rounded-circle cursor-pointer px-2 py-2" @click="comment_mute_settings_modal = false">
                    <Icon icon="fluent:dismiss-12-filled" width="23px" height="23px" />
                </div>
            </v-card-title>
            <div class="px-5 pb-5">
                <div class="text-subtitle-1 d-flex align-center font-weight-bold mt-4">
                    <Icon icon="fluent:comment-dismiss-20-filled" width="24px" />
                    <span class="ml-2 mr-2">ミュート済みのキーワード</span>
                    <v-btn class="ml-auto" depressed
                        @click="settingsStore.settings.muted_comment_keywords.push({match: 'partial', pattern: ''})">
                        <Icon icon="fluent:add-12-filled" height="17px" />
                        <span class="ml-1">追加</span>
                    </v-btn>
                </div>
                <div class="muted-comment-items">
                    <!-- @eslint-ignore -->
                    <div class="muted-comment-item" v-for="(muted_comment_keyword, index) in settingsStore.settings.muted_comment_keywords"
                        :key="muted_comment_keyword.id">
                        <v-text-field type="search" class="muted-comment-item__input" dense outlined hide-details
                            placeholder="ミュートするキーワードを入力"
                            v-model="settingsStore.settings.muted_comment_keywords[index].pattern">
                        </v-text-field>
                        <v-select class="muted-comment-item__match-type" dense outlined hide-details
                            :items="muted_comment_keyword_match_type"
                            v-model="settingsStore.settings.muted_comment_keywords[index].match">
                        </v-select>
                        <button v-ripple class="muted-comment-item__delete-button"
                            @click="settingsStore.settings.muted_comment_keywords
                                .splice(settingsStore.settings.muted_comment_keywords.indexOf(muted_comment_keyword), 1)">
                            <Icon icon="fluent:delete-16-filled" width="20px" />
                        </button>
                    </div>
                </div>
                <div class="text-subtitle-1 d-flex align-center font-weight-bold mt-4">
                    <Icon icon="fluent:person-prohibited-20-filled" width="24px" />
                    <span class="ml-2 mr-2">ミュート済みのニコニコユーザー ID</span>
                    <v-btn class="ml-auto" depressed
                        @click="settingsStore.settings.muted_niconico_user_ids.push('')">
                        <Icon icon="fluent:add-12-filled" height="17px" />
                        <span class="ml-1">追加</span>
                    </v-btn>
                </div>
                <div class="muted-comment-items">
                    <div class="muted-comment-item" v-for="(muted_niconico_user_id, index) in settingsStore.settings.muted_niconico_user_ids"
                        :key="muted_niconico_user_id.id">
                        <v-text-field type="search" class="muted-comment-item__input" dense outlined hide-details
                            placeholder="ミュートするニコニコユーザー ID を入力" v-model="settingsStore.settings.muted_niconico_user_ids[index]">
                        </v-text-field>
                        <button v-ripple class="muted-comment-item__delete-button"
                            @click="settingsStore.settings.muted_niconico_user_ids
                                .splice(settingsStore.settings.muted_niconico_user_ids.indexOf(muted_niconico_user_id), 1)">
                            <Icon icon="fluent:delete-16-filled" width="20px" />
                        </button>
                    </div>
                </div>
                <div class="text-subtitle-1 d-flex align-center font-weight-bold mt-4">
                    <Icon icon="fa-solid:sliders-h" width="24px" height="20px" />
                    <span class="ml-2">クイック設定</span>
                </div>
                <div class="settings__item settings__item--switch">
                    <label class="settings__item-heading" for="mute_vulgar_comments">
                        露骨な表現を含むコメントをミュートする
                    </label>
                    <label class="settings__item-label" for="mute_vulgar_comments">
                        性的な単語などの露骨・下品な表現を含むコメントを、一括でミュートするかを設定します。<br>
                    </label>
                    <v-switch class="settings__item-switch" id="mute_vulgar_comments" inset hide-details
                        v-model="settingsStore.settings.mute_vulgar_comments">
                    </v-switch>
                </div>
                <div class="settings__item settings__item--switch">
                    <label class="settings__item-heading" for="mute_abusive_discriminatory_prejudiced_comments">
                        罵倒や誹謗中傷、差別的な表現、政治的に偏った表現を含むコメントをミュートする
                    </label>
                    <label class="settings__item-label" for="mute_abusive_discriminatory_prejudiced_comments">
                        『死ね』『殺す』などの罵倒や誹謗中傷、特定の国や人々への差別的な表現、政治的に偏った表現を含むコメントを、一括でミュートするかを設定します。<br>
                    </label>
                    <v-switch class="settings__item-switch" id="mute_abusive_discriminatory_prejudiced_comments" inset hide-details
                        v-model="settingsStore.settings.mute_abusive_discriminatory_prejudiced_comments">
                    </v-switch>
                </div>
                <div class="settings__item settings__item--switch">
                    <label class="settings__item-heading" for="mute_big_size_comments">
                        文字サイズが大きいコメントをミュートする
                    </label>
                    <label class="settings__item-label" for="mute_big_size_comments">
                        通常より大きい文字サイズで表示されるコメントを、一括でミュートするかを設定します。<br>
                        文字サイズが大きいコメントには迷惑なコメントが多いです。基本的にはオンにしておくことをおすすめします。<br>
                    </label>
                    <v-switch class="settings__item-switch" id="mute_big_size_comments" inset hide-details
                        v-model="settingsStore.settings.mute_big_size_comments">
                    </v-switch>
                </div>
                <div class="settings__item settings__item--switch">
                    <label class="settings__item-heading" for="mute_fixed_comments">
                        映像の上下に固定表示されるコメントをミュートする
                    </label>
                    <label class="settings__item-label" for="mute_fixed_comments">
                        映像の上下に固定された状態で表示されるコメントを、一括でミュートするかを設定します。<br>
                        固定表示されるコメントが煩わしいと感じる方は、オンにしておくことをおすすめします。<br>
                    </label>
                    <v-switch class="settings__item-switch" id="mute_fixed_comments" inset hide-details
                        v-model="settingsStore.settings.mute_fixed_comments">
                    </v-switch>
                </div>
                <div class="settings__item settings__item--switch">
                    <label class="settings__item-heading" for="mute_colored_comments">
                       色付きのコメントをミュートする
                    </label>
                    <label class="settings__item-label" for="mute_colored_comments">
                        白以外の色で表示される色付きのコメントを、一括でミュートするかを設定します。<br>
                        この設定をオンにしておくと、目立つ色のコメントを一掃できます。<br>
                    </label>
                    <v-switch class="settings__item-switch" id="mute_colored_comments" inset hide-details
                        v-model="settingsStore.settings.mute_colored_comments">
                    </v-switch>
                </div>
                <div class="settings__item settings__item--switch">
                    <label class="settings__item-heading" for="mute_consecutive_same_characters_comments">
                        8文字以上同じ文字が連続しているコメントをミュートする
                    </label>
                    <label class="settings__item-label" for="mute_consecutive_same_characters_comments">
                        『wwwwwwwwwww』『あばばばばばばばばば』など、8文字以上同じ文字が連続しているコメントを、一括でミュートするかを設定します。<br>
                        しばしばあるテンプレコメントが煩わしいと感じる方は、オンにしておくことをおすすめします。<br>
                    </label>
                    <v-switch class="settings__item-switch" id="mute_consecutive_same_characters_comments" inset hide-details
                        v-model="settingsStore.settings.mute_consecutive_same_characters_comments">
                    </v-switch>
                </div>
            </div>
        </v-card>
    </v-dialog>
</template>
<script lang="ts">

import { mapStores } from 'pinia';
import Vue, { PropType } from 'vue';

import useSettingsStore from '@/store/SettingsStore';

export default Vue.extend({
    name: 'CommentMuteSettings',
    // カスタム v-model を実装する
    // ref: https://jp.vuejs.org/v2/guide/components-custom-events.html
    model: {
        prop: 'showing',  // v-model で渡された値が "showing" props に入る
        event: 'change',  // "change" イベントで親コンポーネントに反映
    },
    props: {
        // コメントのミュート設定のモーダルを表示するか
        showing: {
            type: Boolean as PropType<Boolean>,
            required: true,
        }
    },
    data() {
        return {

            // インターバルのタイマー ID
            interval_timer_id: 0,

            // コメントのミュート設定のモーダルを表示するか
            comment_mute_settings_modal: false,

            // ミュート済みのキーワードのマッチタイプ
            muted_comment_keyword_match_type: [
                {text: '部分一致', value: 'partial'},
                {text: '前方一致', value: 'forward'},
                {text: '後方一致', value: 'backward'},
                {text: '完全一致', value: 'exact'},
                {text: '正規表現', value: 'regex'},
            ],
        }
    },
    computed: {
        // SettingsStore に this.settingsStore でアクセスできるようにする
        // ref: https://pinia.vuejs.org/cookbook/options-api.html
        ...mapStores(useSettingsStore),
    },
    watch: {

        // showing (親コンポーネント側) の変更を監視し、変更されたら comment_mute_settings_modal に反映する
        showing() {
            this.comment_mute_settings_modal = this.showing as boolean;
        },

        // comment_mute_settings_modal (子コンポーネント側) の変更を監視し、変更されたら this.$emit() で親コンポーネントに伝える
        comment_mute_settings_modal() {
            this.$emit('change', this.comment_mute_settings_modal);
        }
    }
});

</script>
<style lang="scss" scoped>

.comment-mute-settings {
    .v-card__title, & > div {
        @include smartphone-vertical {
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
    }
}

// views/Settings/Base.vue から抜粋して一部編集
.settings__item {
    display: flex;
    position: relative;
    flex-direction: column;
    margin-top: 24px;
    @include smartphone-horizontal {
        margin-top: 16px;
    }

    &--switch {
        margin-right: 62px;
    }

    &-heading {
        display: flex;
        align-items: center;
        color: var(--v-text-base);
        font-size: 16.5px;
        @include smartphone-horizontal {
            font-size: 15px;
        }
    }
    &-label {
        margin-top: 8px;
        color: var(--v-text-darken1);
        font-size: 13.5px;
        line-height: 1.6;
        @include smartphone-horizontal {
            font-size: 11px;
            line-height: 1.7;
        }
    }
    &-form {
        margin-top: 14px;
        @include smartphone-horizontal {
            font-size: 13.5px;
        }
    }
    &-switch {
        align-items: center;
        position: absolute;
        top: 0;
        right: -74px;
        bottom: 0;
        margin-top: 0;
    }

    p {
        margin-bottom: 8px;
        &:last-of-type {
            margin-bottom: 0px;
        }
    }
}
.muted-comment-items {
    display: flex;
    flex-direction: column;
    margin-top: 8px;

    .muted-comment-item {
        display: flex;
        align-items: center;
        padding: 6px 0px;
        border-bottom: 1px solid var(--v-background-lighten2);
        transition: background-color 0.15s ease;

        &:last-of-type {
            border-bottom: none;
        }

        &__input {
            font-size: 14px;
        }

        &__match-type {
            max-width: 150px;
            margin-left: 12px;
            font-size: 14px;
            @include smartphone-vertical {
                max-width: 115px;
            }
        }

        &__delete-button {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            margin-left: 6px;
            border-radius: 5px;
            outline: none;
            cursor: pointer;
        }
    }
}

</style>