var MAX_WIDTH = 1200;
var QUALITY = 80;

function compressImage(filePath) {
  return new Promise(function(resolve, reject) {
    wx.compressImage({
      src: filePath,
      quality: QUALITY,
      compressedWidth: MAX_WIDTH,
      success: function(res) {
        resolve(res.tempFilePath);
      },
      fail: function(err) {
        resolve(filePath);
      }
    });
  });
}

function chooseImages(count) {
  return new Promise(function(resolve, reject) {
    wx.chooseMedia({
      count: count || 2,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: function(res) {
        var files = res.tempFiles || [];
        resolve(files.map(function(f) { return f.tempFilePath; }));
      },
      fail: function(err) {
        reject(err);
      }
    });
  });
}

function compressAndChoose(count) {
  return chooseImages(count).then(function(paths) {
    var tasks = paths.map(function(p) { return compressImage(p); });
    return Promise.all(tasks);
  });
}

module.exports = {
  compressImage: compressImage,
  chooseImages: chooseImages,
  compressAndChoose: compressAndChoose,
  MAX_WIDTH: MAX_WIDTH,
  QUALITY: QUALITY
};
