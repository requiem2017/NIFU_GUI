import tkinter as tk
import threading
from NIFU_Serial import Pump, Balance, PLC
from NIFU_pid import pid_control, excel_file, graph
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from time import sleep

#replace with correct values
pump1_controller = {'set_point': None, 'kp': 0.1, 'ki': 0.0001, 'kd': 0.01, 'integral_error_limit': 100}
pump2_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump3_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump4_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump5_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump6_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump7_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump8_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump9_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump10_controller = {'set_point': None, 'kp': 1, 'ki': 1, 'kd': 1, 'integral_error_limit': 100}
pump_controllers = [pump1_controller, pump2_controller, pump3_controller, pump4_controller, pump5_controller,
                    pump6_controller, pump7_controller, pump8_controller, pump9_controller, pump10_controller]
matrix_lengths = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]

class NIFU_Synthesis:
    def __init__(self):
        self.root = tk.Tk()
        tk.Label(self.root, text="NIFU SYNTHESIS", font=('Arial',18, 'bold')).pack(pady=10)

        vscrollbar = tk.Scrollbar(self.root, orient='vertical')
        vscrollbar.pack(fill='y', side='right', expand=False)
        hscrollbar = tk.Scrollbar(self.root, orient='horizontal')
        hscrollbar.pack(fill='x', side='bottom', expand=False)
        canvas = tk.Canvas(self.root, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        vscrollbar.config(command=canvas.yview)
        hscrollbar.config(command=canvas.xview)

        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        self.interior = tk.Frame(canvas)
        canvas.create_window(0,0, window=self.interior, anchor='nw')

        def configure_interior(event):
            # Update the scrollbars to match the size of the inner frame.
            size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the canvas's width to fit the inner frame.
                canvas.config(width=self.interior.winfo_reqwidth())
            if self.interior.winfo_reqheight() != canvas.winfo_height():
            # Update the canvas's width to fit the inner frame.
                canvas.config(height=self.interior.winfo_reqheight())
        self.interior.bind('<Configure>', configure_interior)

        gui_frame = tk.Frame(self.interior)

        ### ---EQUIPMENT--- ###
        equipment_frame = tk.Frame(gui_frame)
        self.excel_obj = None

        ### --- PUMPS --- ###
        pumps_frame = tk.Frame(equipment_frame)
        tk.Label(equipment_frame, text="Pumps", font=('Arial', 16, 'underline')).pack(anchor='nw', padx=15)
        tk.Label(pumps_frame, text='Connect', font=('Arial', 12, 'bold')).grid(row=0, column=1)
        tk.Label(pumps_frame, text='On', font=('Arial', 12, 'bold')).grid(row=0, column=2)
        tk.Label(pumps_frame, text='Off', font=('Arial', 12, 'bold')).grid(row=0, column=3)
        tk.Label(pumps_frame, text='Flow Rate', font=('Arial', 12, 'bold')).grid(row=0, column=4)
        tk.Label(pumps_frame, text='Set Flow Rate', font=('Arial', 12, 'bold')).grid(row=0, column=5)
        self.pumps_list = ['HNO₃','Acetic anhydride','Furfural','KOH','2MeTHF','Organic',
                            'Aqueous','H₂SO₄','Amionhydantoin','Crude NIFU Out']
        self.pump_connect_vars = [False] * len(self.pumps_list)
        self.pump_connect_buttons = []
        self.pump_sers = [None] * len(self.pumps_list)
        self.balance_sers = [None] * len(self.pumps_list)
        self.pump_on_buttons = []
        self.pump_off_buttons = []
        self.pump_flow_entry_vars = []

        self.pump_pid_classes = [None] * len(self.pumps_list)
        self.pump_pid_threads_started = [False] * len(self.pumps_list)
        self.pid_vars = [tk.BooleanVar(value=True) for i in self.pumps_list]

        for i, pump_name in enumerate(self.pumps_list):
            # Pump names
            tk.Label(pumps_frame, text=f'Pump {i+1}: {pump_name}').grid(row=i+1, column=0, sticky='w')

            # Connect buttons
            pump_connect_button = tk.Button(pumps_frame, text='Disconnected', width=12, command=lambda i=i: self.pump_connect(i))
            pump_connect_button.grid(row=i+1, column=1, padx=10)
            self.pump_connect_buttons.append(pump_connect_button)

            # On/Off buttons
            pump_on_button = tk.Button(pumps_frame, text='On', width=7, command=lambda i=i: self.pump_on(i))
            pump_off_button = tk.Button(pumps_frame, text='Off', width=7, command=lambda i=i: self.pump_off(i))
            self.pump_on_buttons.append(pump_on_button)
            self.pump_off_buttons.append(pump_off_button)
            pump_on_button.grid(row=i+1, column=2, padx = 10)
            pump_off_button.grid(row=i+1, column=3, padx=10)

            # Entry for flow rate
            self.pump_flow_entry_var = tk.StringVar()
            pump_flow_entry = tk.Entry(pumps_frame, textvariable=self.pump_flow_entry_var, width=15)
            pump_flow_entry.grid(row=i+1, column=4, padx=10)
            self.pump_flow_entry_vars.append(self.pump_flow_entry_var)

            # Set Flow Rate Button
            pump_set_flow_rate_button = tk.Button(pumps_frame, text='Set', width=5, command=lambda i=i: self.pump_set_flow_rate(i))
            pump_set_flow_rate_button.grid(row=i+1, column=5)

            #use pid or no
            data_types_checkbox = tk.Checkbutton(pumps_frame, text='PID', variable=self.pid_vars[i], command=lambda i=i: self.change_pid_onoff(i))
            data_types_checkbox.grid(row=i+1, column=6)

        pumps_frame.pack(anchor='nw', padx=15)

        self.pump_type_vars = [None for i in self.pumps_list]
        self.pump_port_vars = [None for i in self.pumps_list]
        self.balance_port_vars = [None for i in self.pumps_list]

        ### --- VALVES --- ###
        valves_frame = tk.Frame(equipment_frame)
        tk.Label(equipment_frame, text="3-Way Valves", font=('Arial', 16, 'underline')).pack(anchor='nw', padx=15, pady=(10,0))
        self.valves_dict = {
            'Valve 1: Organic': None,
            'Valve 2: H₂SO₄': None,
            'Valve 3: Aminohydantoin': None
        }
        self.valves_onoff_vars = []

        for i, valve_name in enumerate(self.valves_dict):
            # Valve names
            tk.Label(valves_frame, text=valve_name).grid(row=i, column=0, sticky='w')

            # On/Off buttons
            valves_var = tk.IntVar()
            valves_var.set(1)
            self.valves_onoff_vars.append(valves_var)
            valve_on_button = tk.Radiobutton(valves_frame, text='collection', value=1, variable=valves_var)
            valve_off_button = tk.Radiobutton(valves_frame, text='waste', value=0, variable=valves_var)
            valve_on_button.grid(row=i, column=1)
            valve_off_button.grid(row=i, column=2)

        valves_frame.pack(anchor='nw', padx=15)

        ### --- TEMPERATURES --- ###
        temps_frame = tk.Frame(equipment_frame)
        tk.Label(equipment_frame, text="Reactor Temperatures (°C)", font=('Arial', 16, 'underline')).pack(anchor='nw', padx=15, pady=(10,0))
        self.temps_dict = {
            'Reactor 1: HNO₃': ['off', '0'],
            'Reactor 2: Furfural': ['off', '0'],
            'Reactor 3: KOH': ['off', '0'],
            'Reactor 4: 2MeTHF': ['off', '0'],
            'Reactor 5: H₂SO₄': ['off', '0'],
            'Reactor 6: Aminohydantoin': ['off', '0']
        }
        self.temps_onoff_vars = []
        self.temp_entry_vars = []

        for i, temp_name in enumerate(self.temps_dict):
            # Temp names
            tk.Label(temps_frame, text=temp_name).grid(row=i, column=0, sticky='w')

            # On/Off buttons
            temps_onoff_var = tk.IntVar()
            temps_onoff_var.set(0)  # Initial state: off
            self.temps_onoff_vars.append(temps_onoff_var)
            temp_on_button = tk.Radiobutton(temps_frame, text='on', value=1, variable=temps_onoff_var)
            temp_off_button = tk.Radiobutton(temps_frame, text='off', value=0, variable=temps_onoff_var)
            temp_on_button.grid(row=i, column=1)
            temp_off_button.grid(row=i, column=2)

            # Entry for temperature
            self.temp_entry_var = tk.StringVar()
            temp_entry= tk.Entry(temps_frame, textvariable=self.temp_entry_var)
            temp_entry.grid(row=i, column=3, sticky='e', padx=(15,0))
            self.temp_entry_vars.append(self.temp_entry_var)

        temps_frame.pack(anchor='nw', padx=15)

        ### --- LIQUID LEVELS --- ###
        liquid_frame = tk.Frame(equipment_frame)
        tk.Label(equipment_frame, text="Liquid Levels (mL)", font=('Arial', 16, 'underline')).pack(anchor='nw', padx=15, pady=(10,0))
        self.liquids_dict = {'Organic': '0', 'Aqueous': '0'}

        self.org_var = tk.StringVar()
        self.org_var.set('0')
        self.aq_var = tk.StringVar()
        self.aq_var.set('0')

        tk.Label(liquid_frame, text='Organic: ').grid(row=0, column=0)
        tk.Entry(liquid_frame, textvariable=self.org_var).grid(row=0, column=1, pady=10)
        tk.Label(liquid_frame, text='Aqueous: ').grid(row=1, column=0)
        tk.Entry(liquid_frame, textvariable=self.aq_var).grid(row=1, column=1)

        liquid_frame.pack(anchor='nw', padx=15)

        ### --- STIRRER --- ###
        stirrer_frame = tk.Frame(equipment_frame)
        tk.Label(equipment_frame, text="Stirrer (rpm)", font=('Arial', 16, 'underline')).pack(anchor='nw', padx=15, pady=(10,0))

        self.stirrer_dict = {'Stirrer 1': '0'}
        tk.Label(stirrer_frame, text='Stirrer 1').grid(row=0, column=0)

        self.stirrer_var = tk.StringVar()
        self.stirrer_var.set('0')
        stirrer_entry = tk.Entry(stirrer_frame, textvariable=self.stirrer_var)
        stirrer_entry.grid(row=0, column=1, padx=(15,0), pady=10)

        stirrer_frame.pack(anchor='nw', padx=15)

        # Create the Enter button
        enter_button = tk.Button(self.root, text='Assign and Read Data', command=self.apply_button_click)
        enter_button.place(x=50, y=10)

        equipment_frame.grid(row=0, column=0, sticky='nw')


        ### --- DATA --- ###
        data_frame = tk.Frame(gui_frame)
        tk.Label(data_frame, text="Graph Data", font=('Arial', 16, 'underline')).grid(row=0, column=0, pady=10, sticky='nw')

        self.plot_temperatures = {'HNO₃':[False, False, []],
                                  'Furfural':[False, False, []],
                                  'KOH':[False, False, []],
                                  '2MeTHF':[False, False, []],
                                  'Aq-Org Separator':[False, False, []],
                                  'H₂SO₄':[False, False, []],
                                  'Aminohydantoin':[False, False, []]
                                  }
        self.plot_pressures = {'HNO₃':[False, False, []],
                               'Furfural':[False, False, []],
                               'KOH':[False, False, []],
                               'H₂SO₄':[False, False, []],
                               'Aminohydantoin':[False, False, []]
                               }
        self.plot_balances = {'HNO₃':[False, False, []],
                              'Acetic anhydride':[False, False, []],
                              'Furfural':[False, False, []],
                              'KOH':[False, False, []],
                              '2MeTHF':[False, False, []],
                              'Aqueous':[False, False, []],
                              'H₂SO₄':[False, False, []],
                              'Aminohydantoin':[False, False, []],
                              'Crude NIFU Out':[False, False, []]
                              }
        self.plot_flow_rates = {'HNO₃':[False, False, []],
                                'Acetic anhydride':[False, False, []],
                                'Reactor 1':[False, False, []],
                                'Furfural':[False, False, []],
                                'KOH':[False, False, []],
                                '2MeTHF':[False, False, []],
                                'H₂SO₄':[False, False, []],
                                'Aminohydantoin':[False, False, []],
                                'Crude NIFU Out':[False, False, []]
                                }
        self.data_type_dict_objects = [self.plot_temperatures, self.plot_pressures, self.plot_balances, self.plot_flow_rates]

        self.g = graph(self.plot_temperatures, self.plot_pressures, self.plot_balances, self.plot_flow_rates)

        #Checkboxes for different data
        data_types_frame = tk.Frame(data_frame)
        self.data_types = ['Temperature', 'Pressure', 'Balance', 'Flow_Rate']
        self.data_types_vars = [tk.BooleanVar() for data_type in self.data_types]
        for index, value in enumerate(self.data_types):
            data_types_checkbox = tk.Checkbutton(data_types_frame, text=value, variable=self.data_types_vars[index],
                                                 command=lambda v=value: self.g.big_checkmark(v))
            data_types_checkbox.grid(row=0, column=index)
            self.data_types_vars[index].trace_add('write', self.update_plot_checkboxes)
        data_types_frame.grid(row=1, column=0, sticky='w')

        #graph and graph buttons
        graph_frame = tk.Frame(data_frame)
        graph_frame.columnconfigure(0, weight=4)
        graph_frame.columnconfigure(1, weight=1)

        # graph_display
        self.graph_display_frame = tk.Frame(graph_frame, width=800, height=500, bg='white')
        self.figure = Figure(figsize = (10,7), dpi = 100)
        plot1 = self.figure.add_subplot(221)
        plot2 = self.figure.add_subplot(222)
        plot3 = self.figure.add_subplot(223)
        plot4 = self.figure.add_subplot(224)

        plot1.set_title('Temperature Over Time')
        plot1.set_xlabel('Time (s)')
        plot1.set_ylabel('Temperature (°C)')

        plot2.set_title('Pressure Over Time')
        plot2.set_xlabel('Time (s)')
        plot2.set_ylabel('Pressure (psi)')

        plot3.set_title('Balance Over Time')
        plot3.set_xlabel('Time (s)')
        plot3.set_ylabel('Balance (g)')

        plot4.set_title('Flow Rate Over Time')
        plot4.set_xlabel('Time (s)')
        plot4.set_ylabel('Flow Rate (mL/min)')
        

        self.plots = [plot1, plot2, plot3, plot4]
        self.figure.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_display_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        #graph_buttons_table
        graph_buttons_table_frame = tk.Frame(graph_frame)

        #buttons
        self.start_button = tk.Button(graph_buttons_table_frame, text='Start', width=20, command=self.change_start_button)
        self.start_button.grid(row=0, column=0)
        self.stop_button = tk.Button(graph_buttons_table_frame, text='Stop', width=20, activebackground='IndianRed1', command=self.change_stop_button)
        self.stop_button.grid(row=1, column=0)
        self.start_excel_button = tk.Button(graph_buttons_table_frame, text='Start Reading Data', width=20, command=self.start_excel)
        self.start_excel_button.grid(row=2, column=0)
        self.stop_excel_button = tk.Button(graph_buttons_table_frame, text='End Reading Data', width=20, activebackground='IndianRed1', command=self.stop_excel)
        self.stop_excel_button.grid(row=3, column=0)

        #table
        tk.Text(graph_buttons_table_frame, width=30, height=23, bg='gray').grid(row=4, column=0, pady=(25,0))

        self.graph_display_frame.grid(row=0, column=0, sticky='N')
        graph_buttons_table_frame.grid(row=0, column=1, sticky='n', padx=20)
        graph_frame.grid(row=2, column=0, sticky='w')

        #Checkboxes for what to plot
        tk.Label(data_frame, text='Plot:',font=('Arial', 16, 'underline')).grid(row=3, column=0, pady=10, sticky='nw')
        self.plot_frame = tk.Frame(data_frame)

        # Temperature checkboxes
        self.plot_temperature_name = tk.Label(self.plot_frame, text='Temperature:')
        self.plot_temperature_name.grid(row=0, column=0, sticky='nw')
        self.plot_temperature_name.grid_remove()

        self.plot_temperatures_vars = [tk.BooleanVar() for _ in self.plot_temperatures]
        self.plot_temperatures_checkboxes = []
        self.plot_temperatures_frame = tk.Frame(self.plot_frame)

        for index, value in enumerate(self.plot_temperatures):
            plot_temperatures_checkbox = tk.Checkbutton(self.plot_temperatures_frame, text=value, variable=self.plot_temperatures_vars[index],
                                                        command=lambda v=value: self.g.checkmark('Temperature', v))
            self.plot_temperatures_checkboxes.append(plot_temperatures_checkbox)
            plot_temperatures_checkbox.grid(row=0, column=index, sticky='w')
            plot_temperatures_checkbox.grid_remove()

        self.plot_temperatures_frame.grid(row=0, column=1, sticky='w')

        # Pressure checkboxes
        self.plot_pressure_name = tk.Label(self.plot_frame, text='Pressure:')
        self.plot_pressure_name.grid(row=1, column=0, sticky='nw')
        self.plot_pressure_name.grid_remove()

        self.plot_pressures_vars = [tk.BooleanVar() for _ in self.plot_pressures]
        self.plot_pressures_checkboxes = []
        self.plot_pressures_frame = tk.Frame(self.plot_frame)

        for index, value in enumerate(self.plot_pressures):
            plot_pressures_checkbox = tk.Checkbutton(self.plot_pressures_frame, text=value, variable=self.plot_pressures_vars[index],
                                                        command=lambda v=value: self.g.checkmark('Pressure', v))
            self.plot_pressures_checkboxes.append(plot_pressures_checkbox)
            plot_pressures_checkbox.grid(row=0, column=index, sticky='w')
            plot_pressures_checkbox.grid_remove()

        self.plot_pressures_frame.grid(row=1, column=1, sticky='w')

        # Balance checkboxes
        self.plot_balance_name = tk.Label(self.plot_frame, text='Balance:')
        self.plot_balance_name.grid(row=2, column=0, sticky='nw')
        self.plot_balance_name.grid_remove()

        self.plot_balances_vars = [tk.BooleanVar() for _ in self.plot_balances]
        self.plot_balances_checkboxes = []
        self.plot_balances_frame = tk.Frame(self.plot_frame)

        for index, value in enumerate(self.plot_balances):
            plot_balances_checkbox = tk.Checkbutton(self.plot_balances_frame, text=value, variable=self.plot_balances_vars[index],
                                                        command=lambda v=value: self.g.checkmark('Balance', v))
            self.plot_balances_checkboxes.append(plot_balances_checkbox)
            plot_balances_checkbox.grid(row=0, column=index, sticky='w')
            plot_balances_checkbox.grid_remove()

        self.plot_balances_frame.grid(row=2, column=1, sticky='w')

        # Flow rate checkboxes
        self.plot_flowrate_name = tk.Label(self.plot_frame, text='Flow Rate:')
        self.plot_flowrate_name.grid(row=3, column=0, sticky='nw')
        self.plot_flowrate_name.grid_remove()

        self.plot_flow_rates_vars = [tk.BooleanVar() for _ in self.plot_flow_rates]
        self.plot_flow_rates_checkboxes = []
        self.plot_flow_rates_frame = tk.Frame(self.plot_frame)

        for index, value in enumerate(self.plot_flow_rates):
            plot_flow_rates_checkbox = tk.Checkbutton(self.plot_flow_rates_frame, text=value, variable=self.plot_flow_rates_vars[index],
                                                        command=lambda v=value: self.g.checkmark('Flow_Rate', v))
            self.plot_flow_rates_checkboxes.append(plot_flow_rates_checkbox)
            plot_flow_rates_checkbox.grid(row=0, column=index, sticky='w')
            plot_flow_rates_checkbox.grid_remove()

        self.plot_flow_rates_frame.grid(row=3, column=1, sticky='w')

        self.plot_frame.grid(row=4, column=0, sticky='w')
        data_frame.grid(row=0, column=1, sticky='nw')

        gui_frame.pack()

        tk.Button(self.root, text='TEST', command=self.test).place(x=10, y=10)
        self.root.bind("<KeyPress>", self.exit_shortcut) #press escape button on keyboard to close the GUI
        self.root.mainloop()


    #equipment functions

    #pumps
    def pump_connect(self, pump_index):
        if not self.pump_connect_vars[pump_index]:  # If not connected
            self.pump_connect_vars[pump_index] = True
            self.pump_connect_buttons[pump_index].config(bg='LightSkyBlue1', text='Connected')  # Change to blue color

            p_ser = Pump.pump_connect(self, self.pump_port_vars[pump_index].get())
            self.pump_sers[pump_index] = p_ser

            b_ser = Balance.balance_connect(self, self.balance_port_vars[pump_index].get())
            self.balance_sers[pump_index] = b_ser

            c = pid_control(b_ser, p_ser, self.pump_type_vars[pump_index].get().upper(), self.pumps_list[pump_index], self.g)
            self.pump_pid_classes[pump_index] = c
            c.set_excel_obj(self.excel_obj)

        else:  # If already connected
            self.pump_connect_vars[pump_index] = False
            self.pump_connect_buttons[pump_index].config(bg='SystemButtonFace', text='Disconnected')  # Change back to default color

            p_ser = self.pump_sers[pump_index]
            Pump.pump_disconnect(self, p_ser)

            b_ser = self.balance_sers[pump_index]
            Balance.balance_disconnect(self, b_ser)

    def pump_on(self, pump_index):
        self.pump_on_buttons[pump_index].config(bg='pale green')
        self.pump_off_buttons[pump_index].config(bg='SystemButtonFace')

        if self.pump_connect_vars[pump_index]: #if connected
            pump_type = self.pump_type_vars[pump_index].get().upper()
            ser=self.pump_sers[pump_index]

            if pump_type == 'ELDEX':
                Pump.eldex_pump_command(self, ser, command='RU')
            elif pump_type == 'UI-22':
                Pump.UI22_pump_command(self, ser, command='G1', value='1')

            c = self.pump_pid_classes[pump_index]
            if c:
                c.set_stop(False)

    def pump_off(self, pump_index): #turning off requires set flow rate to be set again
        self.pump_off_buttons[pump_index].config(bg='IndianRed1')
        self.pump_on_buttons[pump_index].config(bg='SystemButtonFace')

        if self.pump_connect_vars[pump_index]: #if connected
            pump_type = self.pump_type_vars[pump_index].get().upper()

            c = self.pump_pid_classes[pump_index]
            if c:
                c.set_stop(True)

            ser=self.pump_sers[pump_index]
            if pump_type == 'ELDEX':
                Pump.eldex_pump_command(self, ser, command='ST')
            elif pump_type == 'UI-22':
                Pump.UI22_pump_command(self, ser, command='G1', value='0')

    def pump_set_flow_rate(self, index):
        if self.pump_connect_vars[index]: #if connected, assumes pump is on
            flow_rate = float(self.pump_flow_entry_vars[index].get())
            flow_rate = f'{flow_rate:06.3f}'
            pump_type = self.pump_type_vars[index].get().upper()
            p_ser=self.pump_sers[index]
            pump_controller = pump_controllers[index]
            pump_controller['set_point'] = float(flow_rate)

            #figure out excel writing
            if pump_type == 'ELDEX':
                    Pump.eldex_pump_command(self, p_ser, command='SF', value=flow_rate)
            elif pump_type == 'UI-22':
                flow_rate = flow_rate.replace('.', '')
                Pump.UI22_pump_command(self, p_ser, command='S3', value=flow_rate)

            c = self.pump_pid_classes[index]
            c.set_controller_and_matrix(pump_controller, matrix_lengths[index])
            c.set_stop(False)

            if not self.pump_pid_threads_started[index]:
                t_pid = threading.Thread(target=c.start)
                t_pid.daemon = True
                t_pid.start()

                self.pump_pid_threads_started[index] = True

    def change_pid_onoff(self,i):
        c = self.pump_pid_classes[i]
        if c:
            c.pid_onoff(self.pid_vars[i].get())
            if not self.pid_vars[i].get():
                print('PID control off')

    def change_valves(self):
        for i, valve_name in enumerate(self.valves_dict):
            # Update status ('collection', or 'waste')
            valve_status = 'collection' if self.valves_onoff_vars[i].get() == 1 else 'waste'
            self.valves_dict[valve_name] = valve_status

    def change_temps(self):
        for i, temp_name in enumerate(self.temps_dict):
            # Update status ('on' or 'off')
            temp_status = 'on' if self.temps_onoff_vars[i].get() == 1 else 'off'
            self.temps_dict[temp_name][0] = temp_status

            # Update temperature
            if temp_status == 'on':
                temperature = self.temp_entry_vars[i].get()
                self.temps_dict[temp_name][1] = temperature
            else:
                self.temps_dict[temp_name][1] = '0'

    def change_liquids(self):
        self.liquids_dict['Organic'] = self.org_var.get()
        self.liquids_dict['Aqueous'] = self.aq_var.get()

    def change_stirrer(self):
        self.stirrer_dict['Stirrer 1'] = self.stirrer_var.get()

    def apply_button_click(self):
        # Update all dictionaries with the current values from the GUI, and open commands page
        self.change_valves()
        self.change_temps()
        self.change_liquids()
        self.change_stirrer()
        self.open_assign()

    def open_assign(self):
        """
        Assigns a pump type and port number to each pump, and has commands to read data
        Outputs a list for pump type, pump port numbers, and balance port numbers, in the order that corresponds with self.pumps_list
        """

        self.assign_page = tk.Toplevel(self.root)
        #pumps and balance
        tk.Label(self.assign_page, text='Assign Pump Types and Ports', font=('Arial', 14)).pack(pady=10)
        pump_frame = tk.Frame(self.assign_page)

        tk.Label(pump_frame, text='Pump Name', font=('TkDefaultFont', 9, 'underline')).grid(row=0, column=0)
        tk.Label(pump_frame, text='Pump Type', font=('TkDefaultFont', 9, 'underline')).grid(row=0, column=1)
        tk.Label(pump_frame, text='Pump Port Number', font=('TkDefaultFont', 9, 'underline')).grid(row=0, column=2)
        tk.Label(pump_frame, text='Balance Port Number', font=('TkDefaultFont', 9, 'underline')).grid(row=0, column=3)

        for i, name in enumerate(self.pumps_list):
            tk.Label(pump_frame, text=name).grid(row=i+1, column=0, padx=5)

            self.pump_type_var = tk.StringVar()
            if self.pump_type_vars[i]: #populate assign page with previously assigned values
                self.pump_type_var.set(self.pump_type_vars[i].get())
            pump_type_entry = tk.Entry(pump_frame, textvariable=self.pump_type_var)
            pump_type_entry.grid(row=i+1, column=1, padx=5)
            self.pump_type_vars[i] = (self.pump_type_var)

            self.pump_port_var = tk.IntVar()
            if self.pump_port_vars[i]:
                self.pump_port_var.set(self.pump_port_vars[i].get())
            pump_port_spinbox = tk.Spinbox(pump_frame, textvariable=self.pump_port_var, from_=0, to=20, wrap=True)
            pump_port_spinbox.grid(row=i+1, column=2, padx=5)
            self.pump_port_vars[i] = (self.pump_port_var)

            #balances
            self.balance_port_var = tk.IntVar()
            if self.balance_port_vars[i]:
                self.balance_port_var.set(self.balance_port_vars[i].get())
            balance_port_spinbox = tk.Spinbox(pump_frame, textvariable=self.balance_port_var, from_=0, to=20, wrap=True)
            balance_port_spinbox.grid(row=i+1, column=3, padx=5)
            self.balance_port_vars[i] = (self.balance_port_var)

        pump_frame.pack(pady=10)

    #graph data functions
    def change_start_button(self):
        self.start_button.config(background='pale green')
        self.stop_button.config(background='SystemButtonFace')
        self.g.gui_plot_stop(False)
        t = threading.Thread(target=self.g.plot, args=(self.plots, self.canvas))
        t.daemon = True
        t.start()

    def change_stop_button(self):
        self.start_button.config(background='SystemButtonFace')
        self.g.gui_plot_stop(True)

    def start_excel(self):
        self.start_excel_button.config(background='pale green')
        self.stop_excel_button.config(background='SystemButtonFace')

        print('Writing data into excel file...')
        self.excel_obj = excel_file(self.pumps_list, pump_controllers, matrix_lengths)
        for c in self.pump_pid_classes:
            if c:
                c.set_excel_obj(self.excel_obj)
        t_excel = threading.Thread(target=self.excel_obj.start_file)
        t_excel.daemon = True
        t_excel.start()

    def stop_excel(self):
        self.start_excel_button.config(background='SystemButtonFace')

        print('Stopping excel file...')
        self.excel_obj.stop_file()

    def update_plot_checkboxes(self, *args):
        frames = [
            (self.plot_temperature_name, self.plot_temperatures_checkboxes, self.plot_temperatures_frame),
            (self.plot_pressure_name, self.plot_pressures_checkboxes, self.plot_pressures_frame),
            (self.plot_balance_name, self.plot_balances_checkboxes, self.plot_balances_frame),
            (self.plot_flowrate_name, self.plot_flow_rates_checkboxes, self.plot_flow_rates_frame),
        ]

        row = 0
        for i, var in enumerate(self.data_types_vars):
            name, checkboxes, frame = frames[i]
            if var.get():
                name.grid(row=row, column=0, sticky='nw')
                frame.grid(row=row, column=1, sticky='w')
                for checkbox in checkboxes:
                    checkbox.grid()
                row += 1
            else:
                name.grid_remove()
                frame.grid_remove()
                for checkbox in checkboxes:
                    checkbox.grid_remove()

    # Other functions
    def exit_shortcut(self, event):
        """Shortcut for exiting all pages"""
        if event.keysym == "Escape":
            quit()

    def test(self):
        plc = PLC()
        plc.connect(port_number= 502) #host = '169.254.92.250'
        plc.reading_onoff(True)
        # t = threading.Thread(target=lambda: plc.read, args=(reg1, reg2)) #replace with real registers
        t = threading.Thread(target=lambda: plc.read(reg1, reg2))#replace with real registers
        t.daemon = True
        t.start()
        sleep(5)
        plc.reading_onoff(False)
        plc.close()
        print('done reading temperatures')
        

NIFU_Synthesis()
