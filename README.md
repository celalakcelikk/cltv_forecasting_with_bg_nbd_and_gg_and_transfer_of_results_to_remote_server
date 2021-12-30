# CLTV Forecasting with BG/NBD & GG and Transfer of Results to Remote Server (BGNBD & GG ile CLTV Tahmini ve Sonuçların Uzak Sunucuya Gönderilmesi)
<p align="center">
  <img src="https://github.com/celalakcelikk/cltv_forecasting_with_bg_nbd_and_gg_and_transfer_of_results_to_remote_server/blob/main/media/cltv.jpeg" alt="cltv"/>
<p>

## İş Problemi

Bir e-ticaret sitesi müşteri aksiyonları için müşterilerinin CLTV değerlerine göre ileriye dönük bir projeksiyon yapılmasını istemektedir.

Elinizdeki veriseti ile 1 aylık yada 6 aylık zaman periyotları içerisinde en çok gelir getirebilecek müşterileri tespit etmek mümkün müdür?

## Veri Seti Hikayesi
* **Online Retail II** isimli veri seti İngiltere merkezli online bir satış mağazasının 01/12/2009 - 09/12/2011 tarihleri arasındaki satışlarını içermektedir.
* Bu şirketin ürün kataloğunda hediyelik eşyalar yer almaktadır. 
* Şirketin müşterilerinin büyük çoğunluğu kurumsal müşterilerdir.

## Veri Seti Değişkenleri
* **Invoice:** Fatura Numarası. Eğer bu kod C ile başlıyorsa işlemin iptal edildiğini ifade eder.
* **StockCode:** Ürün kodu. Her bir ürün için eşsiz numara.
* **Description:** Ürün ismi 
* **Quantity:** Ürün adedi. Faturalardaki ürünlerden kaçar tane satıldığını ifade etmektedir.
* **InvoiceDate:** Fatura tarihi 
* **UnitPrice:** Fatura fiyatı (Sterlin)
* **CustomerID:** Eşsiz müşteri numarası 
* **Country:** Ülke ism
