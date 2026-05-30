var app = getApp();
var storage = require('../../services/storage');
var api = require('../../services/api');
var subjects = require('../../constants/subjects');
var regions = require('../../constants/regions');

var GRADES = [
  { key: 'gao1', label: '高一', desc: '高中第一年' },
  { key: 'gao2', label: '高二', desc: '高中第二年' },
  { key: 'gao3', label: '高三', desc: '高考冲刺年' }
];

Page({
  data: {
    isLoggedIn: false,
    currentStudent: null,
    editingStudent: null,
    showEditor: false,
    grades: GRADES,
    electiveSubjects: [],
    districts: regions.getRegions('shanghai'),
    subjectList: [
      { id: 'physics', name: '物理', selected: false },
      { id: 'chemistry', name: '化学', selected: false },
      { id: 'biology', name: '生物', selected: false },
      { id: 'politics', name: '政治', selected: false },
      { id: 'history', name: '历史', selected: false },
      { id: 'geography', name: '地理', selected: false }
    ],
    selectedGrade: '',
    selectedSubjects: [],
    selectedDistrict: '',
    districtsIndex: -1,
    studentName: '',
    hasJanEnglish: false
  },

  onLoad: function() {
    this.loadStudents();
  },

  onShow: function() {
    this.loadStudents();
  },

  loadStudents: function() {
    var isLoggedIn = app.isLoggedIn();
    var currentStudent = storage.getStudent();

    if (isLoggedIn && app.getCurrentStudentId()) {
      this.loadFromServer();
    } else {
      this.setData({
        isLoggedIn: isLoggedIn,
        currentStudent: currentStudent
      });
    }
  },

  loadFromServer: function() {
    var that = this;
    api.get('/api/students').then(function(res) {
      var students = res.students || res.data || res || [];
      if (!Array.isArray(students)) students = [];
      var currentStudent = students.length > 0 ? students[0] : null;
      if (currentStudent) {
        storage.saveStudent(currentStudent);
      }
      that.setData({
        isLoggedIn: true,
        currentStudent: currentStudent
      });
    }).catch(function(err) {
      console.warn('[StudentManage] load error:', err);
      var localStudent = storage.getStudent();
      that.setData({
        currentStudent: localStudent
      });
    });
  },

  onAddStudent: function() {
    var subjectList = this.data.subjectList.map(function(s) {
      return { id: s.id, name: s.name, selected: false };
    });
    this.setData({
      showEditor: true,
      editingStudent: null,
      studentName: '',
      selectedGrade: '',
      selectedSubjects: [],
      subjectList: subjectList,
      selectedDistrict: '',
      hasJanEnglish: false
    });
  },

  onEditStudent: function(e) {
    var student = e.currentTarget.dataset.student;
    var electiveList = [];
    if (student.selected_subject_1) electiveList.push(student.selected_subject_1);
    if (student.selected_subject_2) electiveList.push(student.selected_subject_2);
    if (student.selected_subject_3) electiveList.push(student.selected_subject_3);

    var subjectList = this.data.subjectList.map(function(s) {
      return { id: s.id, name: s.name, selected: electiveList.indexOf(s.id) >= 0 };
    });

    this.setData({
      showEditor: true,
      editingStudent: student,
      studentName: student.name || '',
      selectedGrade: student.grade || '',
      selectedSubjects: electiveList,
      subjectList: subjectList,
      selectedDistrict: student.district || student.region_code || '',
      hasJanEnglish: student.has_jan_english_exam || false
    });
  },

  onCancelEdit: function() {
    this.setData({ showEditor: false });
  },

  onNameInput: function(e) {
    this.setData({ studentName: e.detail.value });
  },

  onSelectGrade: function(e) {
    this.setData({ selectedGrade: e.currentTarget.dataset.grade });
  },

  onToggleSubject: function(e) {
    var subjectId = e.currentTarget.dataset.subject;
    var selected = this.data.selectedSubjects.slice();
    var idx = selected.indexOf(subjectId);
    if (idx >= 0) {
      selected.splice(idx, 1);
    } else {
      if (selected.length >= 3) {
        wx.showToast({ title: '最多选3门', icon: 'none' });
        return;
      }
      selected.push(subjectId);
    }
    var subjectList = this.data.subjectList.map(function(s) {
      return { id: s.id, name: s.name, selected: selected.indexOf(s.id) >= 0 };
    });
    this.setData({ selectedSubjects: selected, subjectList: subjectList });
  },

  onSelectDistrict: function(e) {
    this.setData({ selectedDistrict: e.currentTarget.dataset.district });
  },

  onDistrictPick: function(e) {
    var idx = parseInt(e.detail.value);
    var dist = regions.getRegions('shanghai')[idx];
    if (dist) {
      this.setData({
        selectedDistrict: dist.id,
        districtsIndex: idx
      });
    }
  },

  onToggleJanEnglish: function() {
    this.setData({ hasJanEnglish: !this.data.hasJanEnglish });
  },

  onSave: function() {
    var that = this;
    var d = that.data;

    if (!d.studentName.trim()) {
      wx.showToast({ title: '请输入姓名', icon: 'none' });
      return;
    }
    if (!d.selectedGrade) {
      wx.showToast({ title: '请选择年级', icon: 'none' });
      return;
    }

    var gradeLabel = GRADES.find(function(g) { return g.key === d.selectedGrade; });
    var subjectNames = d.selectedSubjects.map(function(sid) {
      var s = subjects.ALL_SUBJECTS.find(function(x) { return x.id === sid; });
      return s ? s.name : sid;
    });
    var districtName = '';
    if (d.selectedDistrict) {
      var dist = regions.ALL_REGIONS.find(function(x) { return x.id === d.selectedDistrict; });
      districtName = dist ? dist.name : d.selectedDistrict;
    }

    var studentData = {
      name: d.studentName.trim(),
      grade: d.selectedGrade,
      grade_display: gradeLabel ? gradeLabel.label : d.selectedGrade,
      region_code: d.selectedDistrict || null,
      district_name: districtName || null,
      selected_subject_1: d.selectedSubjects[0] || null,
      selected_subject_2: d.selectedSubjects[1] || null,
      selected_subject_3: d.selectedSubjects[2] || null,
      elective_display: subjectNames.join('、') || '未选科',
      has_jan_english_exam: d.hasJanEnglish
    };

    if (d.isLoggedIn && app.getCurrentStudentId()) {
      that.saveToServer(studentData);
    } else {
      that.saveLocal(studentData);
    }
  },

  saveLocal: function(studentData) {
    var existing = storage.getStudent() || {};
    var merged = Object.assign({}, existing, studentData);
    if (!merged.id) merged.id = 'local_student_1';
    if (!merged.type) merged.type = 'custom';

    storage.saveStudent(merged);
    app.globalData.currentStudent = merged;

    this.setData({
      showEditor: false,
      currentStudent: merged
    });

    wx.showToast({ title: '保存成功', icon: 'success' });
  },

  saveToServer: function(studentData) {
    var that = this;
    var d = that.data;
    var payload = {
      name: studentData.name,
      grade: studentData.grade,
      region_code: studentData.region_code,
      selected_subject_1: studentData.selected_subject_1,
      selected_subject_2: studentData.selected_subject_2,
      selected_subject_3: studentData.selected_subject_3,
      has_jan_english_exam: studentData.has_jan_english_exam
    };

    if (d.editingStudent && d.editingStudent.id) {
      api.put('/api/students/' + d.editingStudent.id, payload).then(function(res) {
        var updated = Object.assign({}, d.editingStudent, studentData, res);
        storage.saveStudent(updated);
        app.globalData.currentStudent = updated;
        that.setData({
          showEditor: false,
          currentStudent: updated
        });
        that.loadFromServer();
        wx.showToast({ title: '保存成功', icon: 'success' });
      }).catch(function(err) {
        console.warn('[StudentManage] update error:', err);
        that.saveLocal(studentData);
      });
    } else {
      api.post('/api/students', payload).then(function(res) {
        var created = Object.assign({}, studentData, res);
        storage.saveStudent(created);
        app.globalData.currentStudent = created;
        that.setData({
          showEditor: false,
          currentStudent: created
        });
        that.loadFromServer();
        wx.showToast({ title: '添加成功', icon: 'success' });
      }).catch(function(err) {
        console.warn('[StudentManage] create error:', err);
        that.saveLocal(studentData);
      });
    }
  }
});
