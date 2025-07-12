from flask import Flask, render_template, request, jsonify, redirect, url_for
import logging
import os
from datetime import datetime

# Projeye özgü import'lar
from config.settings import load_config
from database.mysql import mysql_manager
from database.user_manager import user_manager
from utils.logger import setup_logger

app = Flask(__name__)
app.secret_key = 'aktweetor_secret_key_2024'

# Logger kurulumu
logger = setup_logger()

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/categories')
def categories():
    """Kategori yönetimi sayfası"""
    return render_template('categories.html')

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Kategorileri getir"""
    try:
        categories = mysql_manager.get_categories('icerik')
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/accounts/<account_type>', methods=['GET'])
def get_accounts(account_type):
    """Hesapları getir"""
    try:
        if account_type == 'giris_yapilan':
            users = user_manager.get_all_users()
            accounts = [user['kullanici_adi'] for user in users]
        else:
            targets = mysql_manager.get_all_targets()
            accounts = [target['kullanici_adi'] for target in targets]

        return jsonify({'success': True, 'accounts': accounts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_categories', methods=['POST'])
def save_categories():
    """Kategorileri kaydet"""
    try:
        data = request.json
        accounts = data.get('accounts', [])
        categories_data = data.get('categories', {})
        account_type = data.get('account_type', 'giris_yapilan')

        saved_count = 0
        for account in accounts:
            # Hesabın kategorilerini sil
            mysql_manager.delete_account_categories(account, account_type)

            # Yeni kategorileri ekle
            for category, value in categories_data.items():
                if value and value != 'Belirtilmemiş':
                    mysql_manager.assign_hierarchical_category_to_account(
                        account, account_type, category, None, value
                    )

            saved_count += 1

        return jsonify({'success': True, 'message': f'{saved_count} hesap için kategoriler kaydedildi'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/targets')
def targets():
    """Hedef hesaplar sayfası"""
    return render_template('targets.html')

@app.route('/stats')
def stats():
    """İstatistikler sayfası"""
    return render_template('stats.html')

if __name__ == '__main__':
    # Konfigürasyonu yükle
    try:
        config = load_config()
        logger.info("🚀 AkTweetor Web Arayüzü başlatılıyor...")

        # Web sunucusunu başlat
        app.run(host='0.0.0.0', port=5000, debug=True)

    except Exception as e:
        logger.error(f"❌ Başlatma hatası: {str(e)}")
        print(f"❌ Hata: {str(e)}")