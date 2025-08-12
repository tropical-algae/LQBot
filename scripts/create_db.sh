#!/bin/bash

if [ -f "$SQLLITE_FILE_PATH" ]; then
    echo "数据库文件已存在：$SQLLITE_FILE_PATH"
else
    echo "数据库文件不存在，正在创建..."
    sqlite3 "$SQLLITE_FILE_PATH" ".open $SQLLITE_FILE_PATH" ".exit"
    if [ -f "$SQLLITE_FILE_PATH" ]; then
        echo "数据库文件创建成功：$SQLLITE_FILE_PATH"
    else
        echo "数据库文件创建失败！"
        exit 1
    fi
fi