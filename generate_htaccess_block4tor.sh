#!/bin/bash

# 実行Python
PROGRAM='./generate_htaccess_block4tor_py2.py'

# 宛先サーバアドレス、ポート番号(443/tcp=HTTPS)
TARGET_ADDRESS=`dig @8.8.8.8 0nyx.net +short`
TARGET_PORT='443'

# 最終.htaccess保存場所
HTACCESS_DEST='/var/www/html'

# 既存.htaccessファイルパス(fullpath)
HTACCESS_ORIGINAL='/var/www/.htaccess.org'

# 一時的保存場所
HTACCESS_TEMP='/tmp'

# 過去分を保持する期間
HTACCESS_MTIME_DAYS='+30'

# 差分閾値
# この閾値より大きい場合は.htaccess更新を停止
DIFF_THRESHOLD=300

#------------------------------------------------------------------------------
# 強制実行フラグ
FORCE_WRITE=false

function usage_exit() {
	echo "Usage: $0 [-f]" 1>&2
	exit 1
}

function main() {
#今の日次
	DATETIME=$(date '+%Y%m%d%H%M%S')

	RESULT=$(${PROGRAM} \
	-p ${TARGET_PORT} \
	-e ${HTACCESS_TEMP} \
	${TARGET_ADDRESS})
	RESULT_CODE=$?

	# 次回用に.htaccessを残す
	if [ -e "${HTACCESS_TEMP}/.htaccess" ]; then
		mv -f ${HTACCESS_TEMP}/.htaccess ${HTACCESS_TEMP}/.htaccess.${DATETIME}
	fi

	# 正常終了
	if [ ${RESULT_CODE} -ne 0 ]; then
		echo "[error] error result code : " ${RESULT_CODE}
		return ${RESULT_CODE}
	fi

	echo ${RESULT}
	LIST_COUNT=$(echo ${RESULT} | awk '{print $7}')
	echo "[info] LIST COUNT : " ${LIST_COUNT}
	if [ -e "${HTACCESS_TEMP}/.htaccess.before" -a -e "${HTACCESS_TEMP}/.htaccess.${DATETIME}" ]; then
		DIFF_COUNT=$(diff -c ${HTACCESS_TEMP}/.htaccess.before ${HTACCESS_TEMP}/.htaccess.${DATETIME} | grep -E '^(\-|\+|!)\s' | wc -l)
		echo "[info] DIFF COUNT : " ${DIFF_COUNT}

		if [ ${DIFF_COUNT} -ge ${DIFF_THRESHOLD} ]; then
			echo "[error] Threshold exceeded!"

			if [ "${FORCE_WRITE}" == "false" ]; then
				return 2
			fi

			echo "[warning] force write"
		fi
	fi

	if [ -e "${HTACCESS_ORIGINAL}" ]; then
		# 既存設定を上書き
		cat ${HTACCESS_ORIGINAL} > ${HTACCESS_DEST}/.htaccess.tmp
	fi
	# Torブロックリストを追記
	cat ${HTACCESS_TEMP}/.htaccess.${DATETIME} >> ${HTACCESS_DEST}/.htaccess.tmp

	# 適用状態へ切り替え
	mv ${HTACCESS_DEST}/.htaccess.tmp ${HTACCESS_DEST}/.htaccess

	# 次回用にシンボリックリンク作成
	rm -f ${HTACCESS_TEMP}/.htaccess.before
	ln -s ${HTACCESS_TEMP}/.htaccess.${DATETIME} ${HTACCESS_TEMP}/.htaccess.before

	# 過去分の不要.htaccessを消す
	find ${HTACCESS_TEMP} -type f -mtime ${HTACCESS_MTIME_DAYS} -name '.htaccess*' 2>/dev/null | xargs rm -rf
	echo "[info] success"
	return 0
}

while getopts f OPT
do
	case $OPT in
		f) FORCE_WRITE=true
			;;
		h) usage_exit
			;;
		\?) usage_exit
			;;
	esac
done

# 処理開始
main
