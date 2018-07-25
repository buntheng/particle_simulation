"""This is the final version of the particle simulation program!"""
import numpy as np
import qtpy
from qtpy import QtCore, QtGui, uic, QtWidgets, QtCore
from datetime import datetime
import imageio as imgio
import os
import scipy.ndimage as sp_ndimage
import skimage.draw as si_draw
import skimage.filters as si_filters
import skimage.morphology as si_morphology
import skimage.transform as si_transform
import skimage.util as si_util
import sys

# get main.py path
path = os.path.dirname(os.path.abspath(__file__))

# change current directory
os.chdir(path)

# loading GUi from main_window.ui
form_class = uic.loadUiType("mainwindow.ui")[0]

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    qtpy.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    qtpy.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

class QGraphicsView(QtWidgets.QGraphicsView):
    def __init__ (self, parent):
        super(QGraphicsView, self).__init__ (parent)

        # get reference to MainWindow and all the variables and functions 
        self.main_window = self.parent()
        while self.main_window.objectName() != "MainWindow":
            self.main_window = self.main_window.parent()

    def wheelEvent(self, event):
        if self.scene():
            # Zoom Factor
            zoomInFactor = 1.25
            zoomOutFactor = 1 / zoomInFactor

            # Set Anchors -- make scene stay in the same place 
            self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
            self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)

            # Save the scene position
            oldPos = self.mapToScene(event.pos())

            # get zooming factor
            if event.angleDelta().y() > 0:
                zoomFactor = zoomInFactor
            else:
                zoomFactor = zoomOutFactor
            
            # actual zooming
            self.scale(zoomFactor, zoomFactor)

            # Get the new position
            newPos = self.mapToScene(event.pos())

            # Move scene back to old position
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())

class QTableView(QtWidgets.QTableView):
    def __init__ (self, parent):
        super(QTableView, self).__init__ (parent)

        # get reference to MainWindow and all the variables and functions 
        self.main_window = self.parent()
        while self.main_window.objectName() != "MainWindow":
            self.main_window = self.main_window.parent()

    def mouseReleaseEvent(self, event):
        QtWidgets.QTableView.mouseReleaseEvent(self, event)
        self.main_window.reset_particle_widgets()
        self.main_window.select_particle()
        
class MainWindow(QtWidgets.QMainWindow, form_class): # Ui_MainWindow): #
    def __init__(self, parent=None): # set up widget and main database
        QtWidgets.QMainWindow.__init__(self, parent)
	
        # create and add window.py's widgets to MainWindow        
        self.setupUi(self)

        # set up database
        self.setup_database()

        # set up gui
        self.load_fromButton.clicked.connect(self.load_size)
        self.spin_slider(self.widthSlider, self.widthSpinBox)
        self.spin_slider(self.heightSpinBox, self.heightSlider)


        # set up particle widgets
        self.setup_particleShape()
        self.shapeComboBox.currentIndexChanged.connect(self.shapeComboBox_indexChange)        
        self.spin_slider_double(self.noiseDoubleSpinBox, self.noiseDoubleSlider)
        self.spin_slider(self.rotationSlider, self.rotationSpinBox)
        self.add_particleButton.clicked.connect(self.add_particle)

        self.spin_slider_double(self.bkgDoubleSlider, self.bkgDoubleSpinBox)
        self.spin_slider_double(self.contrastDoubleSpinBox, self.contrastDoubleSlider)
        self.spin_slider_double(self.shadowDoubleSpinBox, self.shadowDoubleSlider)
        self.spin_slider_double(self.gaussianDoubleSpinBox, self.gaussianDoubleSlider)
        self.setup_imageType()
        self.image_typeComboBox.currentIndexChanged.connect(self.change_image)
        # imageViewer
        self.setup_imageViewer()

        # particle_detail
        self.setup_particle_widgets()        
        self.setup_particle_detailTable()
        
        # save
        self.save_imageButton.clicked.connect(self.save_image)
        #self.save_dataButton.clicked.connect(self.save_data)

        self.resetButton.clicked.connect(self.reset_particle)
        self.refreshButton.clicked.connect(self.update_imageViewer)

        self.setWindowTitle("Particle Simulation")
    """
        self.debugPushButton.clicked.connect(self.debug)

    def debug(self):
        major_axeSpinBox = QtWidgets.QSpinBox()
        major_axeSpinBox.setObjectName('major_axeSpinBox')
        major_axeSpinBox.setMaximum(999)


        minor_axeSpinBox = QtWidgets.QSpinBox()
        minor_axeSpinBox.setObjectName('minor_axeSpinBox')
        minor_axeSpinBox.setMaximum(999)

        self.ellipseDialog = self.new_formDialog('Ellipse input',{'Major Axe':major_axeSpinBox, 
            'Minor Axe':minor_axeSpinBox},)
        
        #self.ellipseDialog.exec()            
        self.setup_ellipseSize()
        self.exec_ellipseDialog()"""

    def add_particle(self):
        # add particle to the database

        # get user inputs
        amount =  self.amountSpinBox.value()

        if self.shapeComboBox.currentText() == 'Circle':
            self.rotationSpinBox.setValue(0)
        
        if amount > 0:
            shape = self.shapeComboBox.currentText()
            try:
                size = self.sizeSpinBox.value()
            except:
                size = self.sizeSpinBox.text()
            noise = self.noiseDoubleSpinBox.value()
            rotation = self.rotationSpinBox.value()

            for i in range(amount):
                # generate particle 
                coords = self.generate_shape(shape)
                polygon = self.apply_size(coords, size)
                
                # add particle info to the database
                particle_number = str(len(self.database['particle']))
                
                self.database['particle'][str(particle_number)] = {'shape':shape, 'size':size, 
                    'noise':noise, 'rotation':rotation, 'coords':coords, 'polygon':polygon}

                # display particle on the table
                model = self.particle_detailTable.model()
                row_no = model.rowCount() + 1
                row_data = [ shape, str(size), str(noise), str(rotation)]

                row_item = []
                for ii in row_data:
                    row_item.append(QtGui.QStandardItem(ii))
                
                model.appendRow(row_item)

        self.amountSpinBox.setValue(0)


    def apply_size(self, coords, size):
        if coords is None:
            # in this case we draw a circle
            rr, cc = si_draw.circle(size, size, size)
        elif coords == 'ellipse':
            major, minor = [int(i) for i in size.split(';')]
            # drawing 0 degree ellipse
            rr, cc = si_draw.ellipse(minor, major, minor, major, rotation=0)
        else:
            x = self.shift_coords(size*coords['x'])/4
            y = self.shift_coords(size*coords['y'])/4
            rr, cc = si_draw.polygon(y, x)
            
        return({'rr':rr, 'cc': cc})

    def change_image(self):
        img_type = self.image_typeComboBox.currentText()
        if img_type == 'Binary Image (Particles only)':
            try:
                self.display_image(self.database['binary_image']['name'])
            except:
                imgio.imsave(self.database['binary_image']['name'], self.database['binary_image']['data'])
                self.display_image(self.database['binary_image']['name'])
        elif img_type == 'Particle+Noise':
            try:
                self.display_image(self.database['particle_bkg_image']['name'])
            except:
                imgio.imsave(self.database['particle_bkg_image']['name'], self.database['particle_bkg_image']['data'])
                self.display_image(self.database['particle_bkg_image']['name'])

    def crop_control(self, img, center_x, center_y, half_x, half_y, padding):
        # control noise generated
        # retrun image contain particle with padded noise  
        w = img.shape[1]
        h = img.shape[0]
        
        x_min = center_x - padding*half_x
        if x_min > 0:
            img[:, 0:x_min] = 0

        x_max = center_x + padding*half_x
        if x_max < w:
            img[:, x_max:w] = 0
        
        y_min = center_y - padding*half_y
        if y_min > 0:
            img[0:y_min, :] = 0
        
        y_max = center_y + padding*half_y
        if y_max < h:
            img[y_max:h, :] = 0

        return(img)

    def delete_selected_particle(self):
        # remove selected particle from the database and the particle table
        
        model = self.particle_detailTable.model()
        start = min(self.database['temp']['selected_row'])
        count = (max(self.database['temp']['selected_row']) - min(self.database['temp']['selected_row'])) + 1
        model.removeRows(start, count)

        for i in self.database['temp']['selected_row']:
            del(self.database['particle'][str(i)])

        particle = self.database['particle']
        self.database['particle'] = {}
        ind = 0
        for i in particle:
            self.database['particle'][str(ind)] = particle[i]
            ind += 1 
        self.database['temp'] = {}
        
        self.reset_particle_widgets()

    def draw_particle(self, particle, img):
        w = img.shape[1]
        h = img.shape[0]
        rr = particle['polygon']['rr']
        cc = particle['polygon']['cc']

        not_edge = self.not_edgeCheckBox.isChecked()
        not_attach = self.not_attachCheckBox.isChecked()

        test = 0
        tried = 1
        while test == 0:

            blank = np.zeros_like(img)
            
            rr_i, cc_i = self.rotate_particle(rr, cc, particle['rotation'])
            rr_i, cc_i = rr_i.astype(int), cc_i.astype(int)

            half_x = int(max(cc_i)/2)
            half_y = int(max(rr_i)/2)

            if not_edge:
                x = int(self.rand(half_x, w - half_x))
                y = int(self.rand(half_y, h - half_y))
            else:
                x = self.rand(0,w)
                y = self.rand(0,h)
            
            rr_i = rr_i + y - half_y
            cc_i = cc_i + x - half_x
            
            rr_i, cc_i = self.adjust_index(rr = rr_i, cc = cc_i, width = w, height = h)
            

            if not_attach and sum(img[rr_i, cc_i]) > 0:
                test = 0
                tried += 1
            else:
                blank[rr_i, cc_i] = 1
                blank = self.apply_noise(blank, particle['noise'], (half_x+half_y)/2)
                blank = self.crop_control(blank, x , y, half_x, half_y, padding = 2)
                blank_close = self.closing(blank, size=particle['size'])
                blank_test = self.dilate(blank_close, 5) # padding 5 pixels to make sure the particles don't touch
                if not_attach and sum(img[blank_test.astype(bool)]) > 0: 
                    test = 0
                    tried += 1
                else:
                    img[blank_close.astype(bool)] = 1
                    particle['binary'] = self.crop_center(blank_close, x - half_x, y - half_y)
                    particle['polygon']['rr'], particle['polygon']['cc'] = np.nonzero(particle['binary'])
                    particle['center'] = {'x': x - half_x, 'y': y - half_y}
                    test = 1 # end while cycle 

            if tried == 50:
                self.no_rules()
                tried = -1
                
        return(img)

    def crop_center(self, img, center_x, center_y):
        h, w = img.shape
        xmin = center_x
        xmax = center_x
        ymin = center_y
        ymax = center_y

        while img[ymin, center_x] != 0 or np.sum(img[ymin, :]) != 0:
            if ymin <= 0:
                break
            else:
                ymin -= 1

        while img[ymax, center_x] != 0 or np.sum(img[ymax, :]) != 0:
            if ymax >= h:
                break
            else:
                ymax += 1

        while img[center_y, xmin] != 0 or np.sum(img[:, xmin]) != 0:
            if xmin <= 0:
                break
            else:
                xmin -= 1

        while img[center_y, xmax] == 1 or np.sum(img[:,xmax]) != 0:
            if xmax >= w:
                break
            else:
                xmax += 1

        return (img[ymin+1:ymax, xmin+1:xmax])

    def draw_on(self, add, center_x, center_y, img, option = 'not_edge'):
        x = add.shape[1]
        y = add.shape[0]

        w = img.shape[1]
        h = img.shape[0]
        
        start_x = center_x - int(x/2)
        stop_x = start_x + x

        start_y = center_y - int(y/2)
        stop_y = y + start_y

        if option is 'no_rule':
            if start_x < 0:
                start_x =0
            if stop_x > w:
                res = stop_x - w
                add = add[:, 0:x-res]
                stop_x = w
            if start_y < 0:
                start_y = 0
            if stop_y > h:
                res = stop_y - h
                add = add[0:y-res, :]
                stop_y = h

        img[start_y:stop_y, start_x:stop_x] = add
        return(img)

    def dilate(self, img, val):
        # structure
        struct = si_morphology.disk(val)
        return(si_morphology.binary_dilation(img, struct))

    def load_particle(self, particle, img):
        particle_binary = particle['binary']
        
        not_edge = self.not_edgeCheckBox.isChecked()
        not_attach = self.not_attachCheckBox.isChecked()
        test = 0
        tried = 1

        while test == 0:
            blank = np.zeros_like(img)
            w = img.shape[0]
            h = img.shape[1]

            if not_edge:
                test_1 = 0
                while test_1 == 0:
                    x = int(self.rand(particle['size']*3/2, w - particle['size']*3/2))
                    y = int(self.rand(particle['size']*3/2, h - particle['size']*3/2))
                    blank_particle = np.copy(blank)
                    try:
                        blank_particle = self.draw_on(particle_binary, x,y,blank_particle)
                        test_1 = 1
                    except:
                        pass
            else:
                x = self.rand(0,w)
                y = self.rand(0,h)
                blank_particle = np.copy(blank)
                blank_particle = self.draw_on(particle_binary, x,y,blank_particle)
            
            blank_test = self.dilate(np.copy(blank_particle), 5)

            if not_attach and sum(img[blank_test.astype(bool)]) > 0:
                test = 0
                tried += 1
            else:
                img[blank_particle.astype(bool)] = 1
                test = 1
        
            if tried == 50: 
                self.no_rules()
                tried = -1
        particle['center'] = {'x':x, 'y':y}
        return(img)


    def closing(self, img, val = 0, size=None):
        # structure
        if size != None:
            if size> 20:
                val = 2
            elif size > 10:
                val = 1
            else:
                val = 0
                
        struct = si_morphology.disk(val)
        return(si_morphology.binary_closing(img, struct))

    def adjust_index(self, rr, cc, width, height):
        index_r = rr > 0  
        index_r *= rr < height
        index_c = cc > 0 
        index_c *= cc < width
        index = index_c*index_r
        return(rr[index], cc[index])
    
    def apply_noise(self, img, noise_level, particle_size):
        img = si_util.random_noise(img.astype(bool), mode='salt', amount = noise_level/2)
        img = si_morphology.remove_small_objects(img.astype(bool), (particle_size)**2)
        return(img)

    def coords2pixmap(self, coords):
        rr, cc = coords['rr'], coords['cc']
        try:
            h, w = self.database['temp']['particle_img_size']
        except:
            w = max(cc)*3
            h = max(rr)*3
            self.database['temp']['particle_img_size'] = [h, w]
        
        img = np.zeros([h,w])
        x = int(w/2)
        y = int(h/2)
        
        half_x = int((max(cc)-min(cc))/2)
        half_y = int((max(rr)-min(rr))/2)

        rr = rr + y - half_y - min(rr)
        cc = cc + x - half_x - min(cc)
        img[rr,cc] = 1
        
        name = '.ptc_img.png'
        imgio.imsave(name, img)
        pixmap = QtGui.QPixmap()
        pixmap.load(name)
        os.remove(name)
        
        return(pixmap)

    def display_image(self, image_name):
        # remove all old image
        scene = self.imageViewer.scene()
        scene.clear()
        scene = QtWidgets.QGraphicsScene()
        
        # load and add new image to scene
        pixmap = QtGui.QPixmap()
        pixmap.load(image_name)
        os.remove(image_name)

        scene.addPixmap(pixmap)
        self.imageViewer.setScene(scene)
        self.imageViewer.fitInView(scene.sceneRect(), 1)
    
    def display_particle(self, option=0, particle_polygon=None, img=None):
        # display particle image on either 
        # particleViewer (option == 1)
        # particleViewer_2 (option == 2)
        # both (option == 0)
        if option == 0:
            viewer_widgets = [self.particleViewer, self.particleViewer_2]
            pixmap = self.coords2pixmap(particle_polygon)
        elif option == 1:
            viewer_widgets = [self.particleViewer]
            pixmap = self.coords2pixmap(particle_polygon)
        elif option ==2:
            viewer_widgets = [self.particleViewer_2]
            pixmap = self.coords2pixmap(particle_polygon)

        # save particle as image and load pixmap 
        
        for viewer in viewer_widgets:
            scene = viewer.scene()
            scene.clear()
            scene = QtWidgets.QGraphicsScene()
            
            # load and add new image to scene

            scene.addPixmap(pixmap)
            viewer.setScene(scene)
            viewer.fitInView(scene.sceneRect(), 1)    

    def exec_ellipseDialog(self):
        if self.ellipseDialog.exec():
            major_axe = self.ellipseDialog.children_widget['Major Axe'].value()
            minor_axe = self.ellipseDialog.children_widget['Minor Axe'].value()
            self.sizeSpinBox.setText(str(major_axe)+';'+str(minor_axe))

    def generate_images(self):            
        w = self.widthSpinBox.value()
        h = self.heightSpinBox.value()

        blank_bkg = np.zeros([h, w])
        bkg = np.copy(blank_bkg)
        binary_image = np.copy(blank_bkg)
        # check for particle on the list
        particles = self.database['particle']

        if len(particles) > 0: 
            for i in particles:
                if self.hold_particleCheckBox.isChecked():
                    try:
                        binary_image = self.load_particle(particles[i], binary_image)
                    except:
                        binary_image = self.draw_particle(particles[i], binary_image)
                else:
                    binary_image = self.draw_particle(particles[i], binary_image)
        self.database['binary_image'] = {'data':binary_image, 'name':'binary_image.png'}
        
        # generating background
        bkg_intensity = self.bkgDoubleSpinBox.value()
        if bkg_intensity > 0:
            bkg += si_util.random_noise(blank_bkg, mean=bkg_intensity)

        self.database['bkg_image'] = {'data': bkg, 'name':'background_image.png'}
        
        # shadow
        shadow = self.shadowDoubleSpinBox.value()
        particle_shadow = np.copy(blank_bkg)
        if shadow != 0:
            particle_shadow = self.dilate(binary_image, int(shadow * 20)) - binary_image
            
        # merge particle with the background
        contrast = self.contrastDoubleSpinBox.value()

        particle_bkg = np.copy(bkg)
        if contrast != 1 and contrast != 0:
            particle_bkg[binary_image.astype(bool)] /= 1-contrast
            particle_bkg[particle_shadow.astype(bool)] *= 1-contrast/5
        else:
            particle_bkg[binary_image.astype(bool)] = 1    

        gaussian_sigma = self.gaussianDoubleSpinBox.value()
        if gaussian_sigma > 0:
            particle_bkg = si_filters.gaussian(particle_bkg, sigma = gaussian_sigma)

        self.database['particle_bkg_image'] = {'data': particle_bkg, 'name':'particle_background_image.png'}


    def generate_shape(self, shape):
        if shape == 'Octagon':
            x = np.array([1, 3, 4, 4, 3, 1, 0, 0])
            y = np.array([0, 0, 1, 3, 4, 4, 3, 1])
            """
            x = np.array([-0.5, 0.5, 1, 1, 0.5, -0.5, -1, -1, -0.5]) 
            y = np.array([-1, -1, -0.5, 0.5, 1, 1, 0.5, -0.5, -1])"""
            return {'x':x, 'y':y}
        elif shape == 'Oct-Rand':
            rand_16 = np.random.choice(np.arange(-1/6, 1/6, 0.05), size = 4, replace = False )
            rand_13 = np.random.choice(np.arange(1/3, 1, 0.05), size = 8, replace = False)
            x = (np.array([-rand_13[0], rand_16[0], rand_13[1], 1, rand_13[2], rand_16[1], -rand_13[3], -1]) + 1) * 2
            y = (np.array([rand_13[4], 1, rand_13[5], rand_16[2], -rand_13[6], -1, -rand_13[7], rand_16[3]]) + 1) * 2
            return{'x':x, 'y':y}
        elif shape == 'Square':
            x = np.array([0,4,4,0])
            y = np.array([0,0,4,4])
            """x = np.array([-1, 1, 1, -1])
            y = np.array([1, 1, -1, -1])"""
            return{'x':x, 'y':y}
        elif shape == 'Quadrilateral':
            rand = np.random.choice(np.arange(-1,1,0.05), size = 4, replace = False)
            x = (np.array([rand[0], 1, rand[1], -1]) + 1) * 2
            y = (np.array([1, rand[2], -1, rand[3]]) + 1) * 2
            return{'x':x, 'y':y}
        elif shape == 'Circle':
            return None   
        elif shape == 'Ellipse':
            return 'ellipse'

    def img2pixmap(self, img):
        img_name = '.img.png'
        imgio.imsave(img_name, img)
        pixmap = QtGui.QPixmap()
        pixmap.load(img_name)
        os.remove(img_name)
        return pixmap

    def spin_slider(self, widget_a, widget_b):
        widget_a.valueChanged.connect(self.link_spin_slider)
        widget_b.valueChanged.connect(self.link_spin_slider)
    
    def spin_slider_double(self, widget_a, widget_b):
        widget_a.valueChanged.connect(self.link_spin_slider_double)
        widget_b.valueChanged.connect(self.link_spin_slider_double)

    def link_spin_slider(self):
        # get sender'object name
        sender = self.sender()
        value = int(sender.value())
        sender.setValue(value)
        name = self.sender().objectName().split('S')
        if type(sender) is QtWidgets.QSlider:
            name = name[0] + 'SpinBox'
            spin = self.findChild(QtWidgets.QSpinBox, name)
            spin.setValue(value)
            
        else:
            name = name[0] + 'Slider'
            slider = self.findChild(QtWidgets.QSlider, name)
            slider.setValue(value)

    def link_spin_slider_double(self):
        # get sender'object name
        sender = self.sender()
        value = sender.value()
        name = self.sender().objectName().split('D')
        if type(sender) is QtWidgets.QSlider:
            name = name[0] + 'DoubleSpinBox'
            spin = self.findChild(QtWidgets.QDoubleSpinBox, name)
            spin.setValue(value/100)
            
        else:
            name = name[0] + 'DoubleSlider'
            slider = self.findChild(QtWidgets.QSlider, name)
            slider.setValue(value*100)

    def load_size(self):
        # make a QFileDialog
        file_dialog = QtWidgets.QFileDialog(self, 'Open an image file')
        file_dialog.setNameFilters(['Images (*.png *.PNG *.j* *.J* *.t* *.T*)',"All Files (*)"])
        file_dialog.setFileMode(3)

        test = 0
        while test == 0:
            if file_dialog.exec():
                file_name = file_dialog.selectedFiles()
                try:
                    img = imgio.imread(file_name[0])
                    test = 1
                except:
                    pass
        w = img.shape[1]
        h = img.shape[0]
        
        self.database['size']['w'] = w
        self.database['size']['h'] = h 
        
        # update interface
        self.update_interface()

    def no_rules(self):
        self.not_edgeCheckBox.setCheck(False)
        self.not_attachCheckBox.setCheck(False)

        self.msg_box('The image size is too small for the particle. All rules are ignored',
            'Ignore Rule', 1)

    def msg_box(self, msg, msg_title, msg_type):
        msg_dlg = QtWidgets.QMessageBox()
        msg_dlg.setText(msg)
        msg_dlg.setWindowTitle(msg_title)
        msg_dlg.setIcon(msg_type)
        msg_dlg.exec_()

    def particle_shapeComboBox_indexChange(self):
        shape = self.particle_shapeComboBox.currentText()

        if shape == 'Ellipse':
            size = self.database['temp']['new_particle']['size']
            self.particle_sizeSpinBox = self.switch_class(self.particle_sizeSpinBox, QtWidgets.QLineEdit)
            self.particle_sizeSpinBox.returnPressed.connect(self.update_particleViewer_2)
            self.particle_sizeSpinBox.setText(str(size)+';'+str(size))

            major_axeSpinBox = QtWidgets.QSpinBox()
            major_axeSpinBox.setObjectName('major_axeSpinBox')
            major_axeSpinBox.setMinimum(1)
            major_axeSpinBox.setMaximum(999)
            major_axeSpinBox.setValue(size)

            minor_axeSpinBox = QtWidgets.QSpinBox()
            minor_axeSpinBox.setObjectName('minor_axeSpinBox')
            minor_axeSpinBox.setMinimum(1)
            minor_axeSpinBox.setMaximum(999)
            minor_axeSpinBox.setValue(size)

            self.ellipseDialog = self.new_formDialog('Ellipse input',{'Major Axe':major_axeSpinBox, 
                'Minor Axe':minor_axeSpinBox},)
            
            if self.ellipseDialog.exec():
                major_axe = self.ellipseDialog.children_widget['Major Axe'].value()
                minor_axe = self.ellipseDialog.children_widget['Minor Axe'].value()
                self.particle_sizeSpinBox.setText(str(major_axe)+';'+str(minor_axe))
        
        elif self.database['temp']['new_particle']['shape'] == 'Ellipse':
            size = self.database['temp']['new_particle']['size']
            if type(size) is str:
                major, minor = [int(i) for i in size.split(';')]
                size = int((major + minor)/2)

            self.particle_sizeSpinBox = self.switch_class(self.particle_sizeSpinBox, QtWidgets.QSpinBox)
            self.particle_sizeSpinBox.setMinimum(1)
            self.particle_sizeSpinBox.setMaximum(999)
            self.particle_sizeSpinBox.setValue(size)
            self.particle_sizeSpinBox.editingFinished.connect(self.update_particleViewer_2)
            
        self.update_particleViewer_2()

    def rand(self, mn, mx, step=1):
        return(np.random.choice(np.arange(mn,mx,step), size = 1, replace = False)[0])        

    def reset_particle(self):
        self.setup_particle_detailTable()
        self.setup_database()
        self.update_interface()
        self.update_imageViewer()

    def rotate_particle(self, rr, cc, angle_deg):
        # rr is the y indexes of particles
        # cc is the x indexes of the particles
        # Methode: rotation de reference

        if angle_deg != 0:
            # fit particle to scikit image rotation algorithm
            rr_1 = rr - np.min(rr)
            cc_1 = cc - np.min(cc)
            particle_img = np.zeros([max(rr_1)+1,max(cc_1)+1])
            particle_img[rr_1,cc_1] = 1
            img_out = si_transform.rotate(particle_img, angle_deg, resize = True).astype(int)

            rr_out = np.nonzero(img_out)[0] + np.min(rr)
            cc_out = np.nonzero(img_out)[1] + np.min(cc)
        else:
            rr_out, cc_out = rr, cc

        return(rr_out, cc_out)

    def save_image(self):
        duplicate = self.duplicateSpinBox.value()
        clock = datetime.now().strftime('%y%m%d_%H%M%S')
        img_type = self.image_typeComboBox.currentText()
        if duplicate > 0:
            # get save direction 
            file_dialog = QtWidgets.QFileDialog(self, "Select saving directory: ")
            file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
            file_dialog.setAcceptMode(1)
            file_dialog.setFileMode(2)
            if  file_dialog.exec():
                file_path = file_dialog.selectedFiles()[0]

                for i in range(duplicate):
                    # get image name
                    img_name = file_path + '/' + clock + '_' + str(i+1) + '.png'
                    
                    if img_type == 'Binary Image (Particles only)':
                        if i != 0:
                            del(self.database['binary_image']) 
                        try:
                            # save particle binary image
                            imgio.imsave(img_name, self.database['binary_image']['data'])
                                                   
                        except:
                            # generate new image file
                            self.generate_images()
                            imgio.imsave(img_name, self.database['binary_image']['data'])

                        # remove saved data   

                    elif img_type == 'Particle+Noise':
                        if i != 0:
                            del(self.database['particle_bkg_image']) 
                        try:
                            # save particle with background noise
                            imgio.imsave(img_name, self.database['particle_bkg_image']['data'])

                        except:
                            # generate new image file
                            self.generate_images()
                            imgio.imsave(img_name, self.database['particle_bkg_image']['data'])
                           
        self.change_image()
    
    def setup_database(self):
        self.database = {
            "size": {'w':500, 'h':500},
            "particle": {},
            'temp':{},
        }
    
    def new_formDialog(self,dlg_name, items_dict):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(dlg_name)
        dlg.children_widget = items_dict
        grid = QtWidgets.QGridLayout()
        row = 0
        for i in items_dict:
            if type(items_dict[i]) is not QtWidgets.QSlider:
                label = QtWidgets.QLabel(i)
                grid.addWidget(label, row, 0)
                items_dict[i].setParent(dlg)
                grid.addWidget(items_dict[i], row, 1)
                
            else:
                grid.addWidget(items_dict[i], row, 0, 1, 2)
                items_dict[i].setParent(dlg)
            row += 1
        
        # add buttons
        ok_button = QtWidgets.QPushButton(dlg)
        ok_button.setText('OK')
        grid.addWidget(ok_button, row, 0)
        cancel_button = QtWidgets.QPushButton(dlg)
        cancel_button.setText('Cancel')
        grid.addWidget(cancel_button, row, 1)

        def accept(dlg):
            dlg.accept()
        def reject(dlg):
            dlg.reject()

        ok_button.clicked.connect(dlg.accept)
        cancel_button.clicked.connect(dlg.reject)

        dlg.setLayout(grid)
        return dlg

    def particle_modified(self):
        # compared save temp data 
        try:
            new_size = self.particle_sizeSpinBox.value()
        except:
            new_size = self.particle_sizeSpinBox.text()
        new_shape = self.particle_shapeComboBox.currentText()
        new_noise = self.particle_noiseDoubleSpinBox.value()
        new_rotation = self.particle_rotationSpinBox.value()
        new_data = {'size': new_size, 'shape': new_shape,
            'noise': new_noise, 'rotation': new_rotation}
        try:
            old_data = self.database['temp']['new_particle']
            changed = False
            for key in new_data:
                if new_data[key] != old_data[key]:
                    changed = True
        except:
            changed = True
            
        if changed:
            self.database['temp']['new_particle'] = new_data
        return changed

    def reset_particle_widgets(self):
        # set value to zeros
        self.particle_sizeSpinBox = self.switch_class(self.particle_sizeSpinBox, QtWidgets.QSpinBox)
        self.particle_sizeSpinBox.setValue(0)
        self.particle_shapeComboBox.setCurrentIndex(0)
        self.particle_noiseDoubleSpinBox.setValue(0)
        self.particle_rotationSpinBox.setValue(0)

        self.database['temp'] = {}
        # reset viewer
        viewer_widgets = [self.particleViewer, self.particleViewer_2]
        for viewer in viewer_widgets:
            scene = viewer.scene()
            scene.clear()
            scene = QtWidgets.QGraphicsScene()
            
            viewer.setScene(scene)
            viewer.fitInView(scene.sceneRect(), 1)

    def save_modified_particle(self):
        model = self.particle_detailTable.model()
        for i in self.database['temp']['selected_row']:
            new_data = self.database['temp']['new_particle']
            self.database['particle'][str(i)] = new_data
            
        
            # update particle data
            row_data = [new_data['shape'],
                str(new_data['size']), str(new_data['noise']),
                str(new_data['rotation'])]
            
            row_item = []
            for ii in row_data:
                row_item.append(QtGui.QStandardItem(ii))
            model.removeRow(i)
            model.insertRow(i, row_item)

        self.database['temp']['old_particle'] = new_data
        self.display_particle(option=1, particle_polygon = new_data['polygon'])

    def select_particle(self):
        # show particle detail and update particle detail
        index = self.particle_detailTable.selectedIndexes()
        rows = []

        for ind in index:
            rows.append(ind.row())
        rows = np.unique(rows)
        self.database['temp']['selected_row'] = rows

        if len(rows) != 1:
            #self.reset_particle_widgets()
            
            data = {'size': 5, 'shape': 'Octagon', 'noise': 0.0, 'rotation': 0}
            self.database['temp']['new_particle'] = data
        else:
            # update particle_widgets
            data = self.database['particle'][str(rows[0])]

            self.database['temp']['old_particle'] = data
            self.database['temp']['new_particle'] = data
            self.update_particleSpinBox(data['size'])
            # self.particle_sizeSpinBox.setValue(data['size'])
            self.particle_shapeComboBox.setCurrentIndex(self.particle_shapeComboBox.findText(data['shape']))
            self.particle_noiseDoubleSpinBox.setValue(data['noise'])
            self.particle_rotationSpinBox.setValue(data['rotation'])
            
            # get particle image and display it on both particleViewer
            self.display_particle(option=0, particle_polygon = data['polygon'])        

    def setup_imageType(self):
        self.database['image_type'] = ['Particle+Noise', 'Binary Image (Particles only)']
        for image_type in self.database['image_type']:
            self.image_typeComboBox.addItem(image_type)

    def setup_imageViewer(self):
        self.imageViewer = self.switch_class(self.imageViewer, QGraphicsView)
        scene = QtWidgets.QGraphicsScene(self.imageViewer)
        self.imageViewer.setScene(scene)
        self.imageViewer.setDragMode(1) # enable hand drag when zoom

        # self.update_imageViewer()

    def setup_particleShape(self):
        self.database['particle_shape'] = ['Octagon', 'Oct-Rand', 
            'Square', 'Quadrilateral', 'Circle', 'Ellipse']
        for shape in self.database['particle_shape']:
            self.shapeComboBox.addItem(shape)
            self.particle_shapeComboBox.addItem(shape)

    def setup_particle_widgets(self):  
        self.particleViewer = self.switch_class(self.particleViewer, QGraphicsView)
        self.particleViewer_2 = self.switch_class(self.particleViewer_2, QGraphicsView)
        viewer_widgets = [self.particleViewer, self.particleViewer_2]
        for viewer in viewer_widgets:
            scene = QtWidgets.QGraphicsScene(self.imageViewer)
            viewer.setScene(scene)
            viewer.setDragMode(1) # enable hand drag when zoom
        
        # setup dynamic update on particleViewer_2
        self.particle_sizeSpinBox.editingFinished.connect(self.update_particleViewer_2)
        self.particle_noiseDoubleSpinBox.editingFinished.connect(self.update_particleViewer_2)
        self.particle_rotationSpinBox.editingFinished.connect(self.update_particleViewer_2)
        self.particle_shapeComboBox.currentIndexChanged.connect(self.particle_shapeComboBox_indexChange)

        self.particle_modifyButton.clicked.connect(self.save_modified_particle)
        self.particle_deleteButton.clicked.connect(self.delete_selected_particle)
    
    def setup_particle_detailTable(self):
        self.particle_detailTable = self.switch_class(self.particle_detailTable, QTableView)

        col_name = ['Shape', 'Size', 'Noise', 'Rotation']
        
        col_num = len(col_name)
        model = QtGui.QStandardItemModel(0, col_num, self.particle_detailTable)
        model.setHorizontalHeaderLabels(col_name)
        self.particle_detailTable.setModel(model)

    def setup_ellipseSize(self):
        # temporary change self.sizeSpinBox to QLineEdit
        self.sizeSpinBox = self.switch_class(self.sizeSpinBox, QtWidgets.QLineEdit)
        # self.sizeSpinBox.setReadOnly(True)
        # self.sizeSpinBox.selectionChanged.connect(self.exec_ellipseDialog)
    
    def setup_normalSize(self):
        # turn sizeSpinBox back to norma QSpinBox
        self.sizeSpinBox = self.switch_class(self.sizeSpinBox, QtWidgets.QSpinBox)
        self.sizeSpinBox.setMinimum(1)
        self.sizeSpinBox.setMaximum(999)

    def shapeComboBox_indexChange(self):
        shape = self.shapeComboBox.currentText()
        if shape == 'Ellipse':
            # show input dialog
            # self.setup_ellipseDialog()
            major_axeSpinBox = QtWidgets.QSpinBox()
            major_axeSpinBox.setObjectName('major_axeSpinBox')
            major_axeSpinBox.setMinimum(1)
            major_axeSpinBox.setMaximum(999)


            minor_axeSpinBox = QtWidgets.QSpinBox()
            minor_axeSpinBox.setObjectName('minor_axeSpinBox')
            minor_axeSpinBox.setMinimum(1)
            minor_axeSpinBox.setMaximum(999)

            self.ellipseDialog = self.new_formDialog('Ellipse input',{'Major Axe':major_axeSpinBox, 
                'Minor Axe':minor_axeSpinBox},)
                       
            self.setup_ellipseSize()
            self.exec_ellipseDialog()
        else:
            self.setup_normalSize()

    def shift_coords(self, array):
        mid = max(array)/2
        array[array>mid] += 1
        array[array<mid] -= 1
        
        mn = np.min(array)
        if mn < 0:
            return(array + abs(mn))
        else:
            return array

    def switch_class(self, widget, new_class):
        # change default QGraphicsView class with custom class
        
        # get widget's parent and geometry
        parent = widget.parent()
        geometry = widget.geometry()

        del(widget)
        # create new widget with the same parent and geometry
        widget = new_class(parent)
        widget.setGeometry(geometry)
        widget.show()
        return(widget)

    def update_imageViewer(self):
        self.tabWidget.setCurrentWidget(self.image_viewerTab)
        self.generate_images()
        self.change_image()

    def update_interface(self):
        self.widthSpinBox.setValue(self.database['size']['w'])
        self.heightSpinBox.setValue(self.database['size']['h'])
    
    def update_particleSpinBox(self, size):
        if type(size) == str:
            self.particle_sizeSpinBox = self.switch_class(self.particle_sizeSpinBox, QtWidgets.QLineEdit)
            self.particle_sizeSpinBox.setText(size)
        else:
            self.particle_sizeSpinBox = self.switch_class(self.particle_sizeSpinBox, QtWidgets.QSpinBox)
            self.particle_sizeSpinBox.setValue(size)

    def update_particleViewer_2(self):
        # redraw particle from the input in particle widgets
        if self.particle_modified():
            update_particleViewer = False
            shape = self.database['temp']['new_particle']['shape']
            size = self.database['temp']['new_particle']['size']
            noise = self.database['temp']['new_particle']['noise']
            rotation = self.database['temp']['new_particle']['rotation']

            coords = self.generate_shape(shape)
            polygon = self.apply_size(coords, size)
            
            rr, cc = polygon['rr'], polygon['cc']
            rr_i, cc_i = self.rotate_particle(rr, cc, rotation)
            
            half_x = np.ceil((max(cc_i)-min(cc_i))/2).astype(int)
            half_y = np.ceil((max(rr_i)-min(rr_i))/2).astype(int)

            try:
                # get existing particle shape 
                x = int(self.database['temp']['particle_img_size'][1]/2)
                y = int(self.database['temp']['particle_img_size'][0]/2)
                if x <= 2*half_x or y <= 2*half_y:
                    update_particleViewer = True
                    raise Exception('Particle out of bound.')
                elif x >= 3*half_x or y >= 3*half_y:
                    update_particleViewer = True
                    raise Exception('Refitted image.')
            except:
                w = int(half_x*6)
                h = int(half_y*6)
                self.database['temp']['particle_img_size'] = [h, w]
                x = np.ceil(w/2).astype(int)
                y = np.ceil(h/2).astype(int)

            rr_i = ((rr_i  + y) - half_y) - min(rr_i)
            cc_i = ((cc_i + x) - half_x) - min(cc_i) 

            blank = np.zeros(self.database['temp']['particle_img_size'])
            blank[rr_i, cc_i] = 1

            blank = self.apply_noise(blank, noise, (half_x+half_y)/2)
            blank = self.closing(blank, size=(half_x+half_y)/2)
            particle_binary = self.crop_center(blank, x, y)
            polygon['rr'], polygon['cc'] = np.nonzero(particle_binary)

            self.database['temp']['new_particle'] = { 'shape':shape, 'size': size,'noise': noise,
                'rotation':rotation, 'coords':coords, 'polygon':polygon, 'binary':particle_binary}

            self.display_particle(option=2, particle_polygon=polygon)

            if update_particleViewer:
                self.display_particle(option=1, particle_polygon=self.database['temp']['old_particle']['polygon'])

app = QtWidgets.QApplication(sys.argv)

# Create OUR very own MainWindow
myWindow = MainWindow()
myWindow.show()
app.exec_()
