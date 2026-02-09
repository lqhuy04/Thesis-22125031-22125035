from newspaper import Article

urls = [
    'https://www.tinnhanhchungkhoan.vn/doanh-thu-nam-2025-cua-vinamilk-vnm-dat-63724-ty-dong-cao-nhat-lich-su-cong-ty-post384738.html',
    'https://doanhnhan.baophapluat.vn/vinamilk-vnm-doanh-thu-lap-dinh-lich-su-gan-64-000-ty-xuat-khau-tang-truong-duong-10-quy-lien-tiep.html'
]

for url in urls:
    article = Article(url)
    article.download()
    article.parse()
    print(f"Tiêu đề: {article.title}")
    print(f"Nội dung tóm tắt: {article.text}")
    print("-" * 20)