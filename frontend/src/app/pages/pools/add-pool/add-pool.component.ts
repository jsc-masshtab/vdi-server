import { trigger, style, animate, transition } from '@angular/animations';
import { Component, OnInit, OnDestroy, Inject } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { debounceTime, map } from 'rxjs/operators';

import { WaitService } from '@core/components/wait/wait.service';

import { AddPoolService } from './add-pool.service';

@Component({
  selector: 'vdi-add-pool',
  templateUrl: './add-pool.component.html',
  animations: [
    trigger(
      'animForm', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('150ms', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        style({ opacity: 1 }),
        animate('150ms', style({ opacity: 0 }))
      ])
    ])
  ]
})

export class PoolAddComponent implements OnInit, OnDestroy {

  sub: Subscription;
  public poolSettings;
  public checkValid: boolean = false;
  public error: boolean = false;

  public type: string = 'static';
  public step: string;
  public last: string;

  public data: any;

  public sharedData: FormGroup;
  public staticPool: FormGroup;
  public dynamicPool: FormGroup;
  public guestPool: FormGroup;
  public rdsPool: FormGroup;

  public nodes: FormControl = new FormControl('');

  public search = new FormControl('');
  public warming_vm: FormControl = new FormControl(false);
  public warming_all: boolean = true;

  public auth_dirs: any[] = []

  constructor(
    private addPoolService: AddPoolService,
    private dialogRef: MatDialogRef<PoolAddComponent>,
    private fb: FormBuilder,
    private waitService: WaitService,
    @Inject(MAT_DIALOG_DATA) poolSettings?: any
    ) {
      this.poolSettings = poolSettings;
    }

  ngOnInit() {
    if (this.poolSettings){
      this.initFormsForCopy();
    } else{
      this.getAllAuthenticationDirectory();
    }

    this.search.valueChanges.pipe(
      debounceTime(1000)
    ).subscribe((value) => {

      const props = {};

      if (value) {
        props['verbose_name'] = value;
      }

      this.getData('vms', {
        id_: this.sharedData.get('controller_id').value,
        resource_pool_id: this.sharedData.get('resource_pool_id').value,
        ...props
      });
    })
  }

  private totalSizeValidator() {
    return (group: FormGroup) => {
      if (group.controls['total_size'].value < group.controls['initial_size'].value) {
        return { maxLessInitial: true };
      }
      if (group.controls['total_size'].value < group.controls['increase_step'].value) {
        return { IncreaseLessMax: true };
      }
      if (group.controls['total_size'].value < group.controls['reserve_size'].value) {
        return { ReserveLessMax: true };
      }
    };
  }

  getAllAuthenticationDirectory() {
    this.addPoolService.getAllAuthenticationDirectory().valueChanges.pipe(map(data => data.data.auth_dirs)).subscribe((res) => {
      this.auth_dirs = res
      this.initForms();
    })
  }


  initForms() {
    this.sharedData = this.fb.group({
      verbose_name: ['', [Validators.required, Validators.pattern(/^[а-яА-ЯёЁa-zA-Z0-9.\-]*$/)]],
      connection_types: [[], Validators.required],

      controller_id: ['', Validators.required],
      resource_pool_id: ['', Validators.required]
    });

    this.staticPool = this.fb.group({
      vms: [[], Validators.required]
    });

    this.rdsPool = this.fb.group({
      rds_vm: [[], Validators.required]
    });

    this.dynamicPool = this.fb.group({
      data_pool_id: ['', Validators.required],
      template_id: ['', Validators.required],
      vm_name_template: ['', [Validators.required, Validators.pattern(/^([a-zA-Z]+[a-zA-Z0-9-]*){0,63}$/)]],
      ...this.auth_dirs.length ? { ad_ou: [''] } : {},
      increase_step: [1, [Validators.required, Validators.max(100), Validators.min(1)]],
      reserve_size: [1, [Validators.required, Validators.max(200), Validators.min(1)]],
      initial_size: [1, [Validators.required, Validators.max(200), Validators.min(1)]],
      total_size: [1, [Validators.required, Validators.max(10000), Validators.min(1)]],
      create_thin_clones: true,
      enable_vms_remote_access: true,
      start_vms: true,
      set_vms_hostnames: true,
      ...this.auth_dirs.length ? { include_vms_in_ad: true } : {},
    }, { validators: this.totalSizeValidator() });

    this.guestPool = this.fb.group({
      data_pool_id: ['', Validators.required],
      template_id: ['', Validators.required],
      vm_name_template: ['', [Validators.required, Validators.pattern(/^([a-zA-Z]+[a-zA-Z0-9-]*){0,63}$/)]],
      ...this.auth_dirs.length ? { ad_ou: [''] } : {},
      increase_step: [1, [Validators.required, Validators.max(100), Validators.min(1)]],
      reserve_size: [1, [Validators.required, Validators.max(200), Validators.min(1)]],
      initial_size: [1, [Validators.required, Validators.max(200), Validators.min(1)]],
      total_size: [1, [Validators.required, Validators.max(10000), Validators.min(1)]],
      vm_disconnect_action_timeout: [60, [Validators.required, Validators.min(1)]],
      create_thin_clones: true,
      is_guest: true,
      enable_vms_remote_access: true,
      start_vms: true,
      set_vms_hostnames: true,
      ...this.auth_dirs.length ? { include_vms_in_ad: true } : {},
    }, { validators: this.totalSizeValidator() });

    this.toStep('type');
  }

  public initFormsForCopy(): void {
    const {
        ad_ou,
        connection_types,
        controller,
        create_thin_clones,
        datapool_id,
        enable_vms_remote_access,
        include_vms_in_ad,
        increase_step,
        initial_size,
        is_guest,
        reserve_size,
        resource_pool_id,
        set_vms_hostnames,
        start_vms,
        template_id,
        total_size,
        vm_disconnect_action_timeout,
        vm_name_template
      } = this.poolSettings;

    this.sharedData = this.fb.group({
      verbose_name: [ '' , [Validators.required, Validators.pattern(/^[а-яА-ЯёЁa-zA-Z0-9.\-]*$/)]],
      connection_types: [connection_types, Validators.required],
      controller_id: [controller, Validators.required],
      resource_pool_id: [resource_pool_id, Validators.required]
    });

    this.staticPool = this.fb.group({
      vms: [[], Validators.required]
    });

    this.rdsPool = this.fb.group({
      rds_vm: [[], Validators.required]
    });

    let formObject =   {
      data_pool_id: [datapool_id, Validators.required],
      template_id: [template_id, Validators.required],
      vm_name_template: [vm_name_template, [Validators.required, Validators.pattern(/^([a-zA-Z]+[a-zA-Z0-9-]*){0,63}$/)]],
      increase_step: [increase_step, [Validators.required, Validators.max(100), Validators.min(1)]],
      reserve_size: [reserve_size, [Validators.required, Validators.max(200), Validators.min(1)]],
      initial_size: [initial_size, [Validators.required, Validators.max(200), Validators.min(1)]],
      total_size: [total_size, [Validators.required, Validators.max(10000), Validators.min(1)]],
      ad_ou,
      enable_vms_remote_access,
      start_vms,
      set_vms_hostnames,
      create_thin_clones,
      include_vms_in_ad,
    }

    this.dynamicPool = this.fb.group({
      ...formObject
    }, { validators: this.totalSizeValidator() });

    this.guestPool = this.fb.group({
      ...formObject,
      is_guest,
      vm_disconnect_action_timeout
    }, { validators: this.totalSizeValidator() });

    if (this.poolSettings.pool_type === 'GUEST'){
      this.type = 'guest';
    }else if (this.poolSettings.pool_type === 'AUTOMATED'){
      this.warming_vm.setValue(this.isAnyVmWarmingFieldChecked());
      this.type = 'dynamic';
    }
    this.toStep('static');
  }

  public isAnyVmWarmingFieldChecked(): boolean {
    const {enable_vms_remote_access, start_vms, set_vms_hostnames} = this.poolSettings;
    const checkboxes = [enable_vms_remote_access, start_vms, set_vms_hostnames];
    return checkboxes.some( checkbox => checkbox === true);
  }

  getData(type, data: any = {}) {

    /* комбинирует запросы с разными фильтрами от одной точки входа controllers */

    this.addPoolService.getData(type, data).valueChanges.pipe(map(pools => pools.data.controller[type])).subscribe((res) => {
      this.data[type] = res;

      if (this.data.templates.length !== 0) {
        this.dynamicPool.get('template_id').setValue(this.data['templates'][0]['id']);
        this.guestPool.get('template_id').setValue(this.data['templates'][0]['id']);
      }
    });
  }

  resetData() {
    this.data = {
      connection_types: this.type === 'rds' ? ['RDP', 'NATIVE_RDP'] : ['RDP', 'NATIVE_RDP', 'SPICE', 'SPICE_DIRECT', 'LOUDPLAY'],
      controllers: [],
      resource_pools: [],
      data_pools: [],
      vms: [],
      templates: []
    };
  }

  selectAllVms() {
    this.staticPool.get('vms').setValue(this.data.vms)
  }

  deselectAllVms() {
    this.staticPool.get('vms').setValue([])
  }

  someComplete() {
    return (this.dynamicPool.get('enable_vms_remote_access').value ||
    this.dynamicPool.get('start_vms').value ||
    this.dynamicPool.get('set_vms_hostnames').value ||
    (this.auth_dirs.length ? this.dynamicPool.get('include_vms_in_ad').value : false)) && !this.warming_all;
  }

  public toStep(step: string) {
    this.last = this.step;

    /* Обработка каждого шага */

    switch (step) {
      case 'type': {
        this.step = step;
        /* Установка начальных значений */
        this.resetData();

        this.checkValid = false;
        this.sharedData.reset();
        this.staticPool.reset();
        this.dynamicPool.reset();
        this.guestPool.reset();
        this.rdsPool.reset();

      }
                   break;

      case 'static': {
        this.step = step;
        this.resetData();

        /* Выбор первого типа */

        if (!this.sharedData.get('connection_types').value) {
          this.sharedData.get('connection_types').setValue([this.data['connection_types'][0]]);
        }

        /* Запрос на контроллеры */

        this.addPoolService.getData('controllers').valueChanges.pipe(map(data => data.data['controllers'])).subscribe((res) => {

          this.data['controllers'] = res;

          if (!this.sharedData.get('controller_id').value) {
            this.sharedData.get('controller_id').setValue(this.data['controllers'][0]['id']);
          } else {
            this.sharedData.get('controller_id').setValue(this.sharedData.get('controller_id').value)
          }
        });

        /* Подписка на изменение полей формы для отправки запросов на сервер */

        this.sharedData.controls['controller_id'].valueChanges.subscribe((value) => {

          if (!this.poolSettings){
            this.sharedData.controls['resource_pool_id'].reset(); // Очистка поля под текущим
          }

          if (value) {
            this.getData('nodes', { id_: value });
            this.getData('resource_pools', { id_: value });
          } // запрос данных для выборки в очищенном поле
        });

        this.sharedData.controls['resource_pool_id'].valueChanges.subscribe((value) => {
          this.staticPool.controls['vms'].reset();

          if (value) {
            this.getData('vms', {
              id_: this.sharedData.get('controller_id').value,
              resource_pool_id: this.sharedData.get('resource_pool_id').value
            });
          }
        });

        this.nodes.valueChanges.subscribe((value) => {

          this.staticPool.get('vms').setValue(null);

          const props = {};

          if (value) {
            props['node_id'] = value;
          }

          this.getData('vms', {
            id_: this.sharedData.get('controller_id').value,
            resource_pool_id: this.sharedData.get('resource_pool_id').value,
            ...props
          });

          console.log(this.staticPool.get('vms').value)
        });

        this.sharedData.controls['resource_pool_id'].valueChanges.subscribe((value) => {

          this.dynamicPool.controls['data_pool_id'].reset(); // Очистка поля под текущим
          this.guestPool.controls['data_pool_id'].reset(); // Очистка поля под текущим

          if (value) {
            this.getData('data_pools', {
              id_: this.sharedData.get('controller_id').value,
              resource_pool_id: value
            });
          } // запрос данных для выборки в очищенном поле
        });

        if (this.poolSettings && this.poolSettings.resource_pool_id) {
          this.getData('data_pools', {
            id_: this.sharedData.get('controller_id').value,
            resource_pool_id: this.poolSettings.resource_pool_id
          });
        }

        if (this.poolSettings && this.poolSettings.datapool_id) {
         this.getData('templates', {
              id_: this.sharedData.get('controller_id').value,
              resource_pool_id: this.sharedData.get('resource_pool_id').value,
              data_pool_id: this.poolSettings.datapool_id
            });
        }
        this.dynamicPool.controls['data_pool_id'].valueChanges.subscribe((value) => {
          this.dynamicPool.controls['template_id'].reset();

          if (value) {
            this.getData('templates', {
              id_: this.sharedData.get('controller_id').value,
              resource_pool_id: this.sharedData.get('resource_pool_id').value,
              data_pool_id: value
            });
          }
        });

        this.guestPool.controls['data_pool_id'].valueChanges.subscribe((value) => {
          this.guestPool.controls['template_id'].reset();

          if (value) {
            this.getData('templates', {
              id_: this.sharedData.get('controller_id').value,
              resource_pool_id: this.sharedData.get('resource_pool_id').value,
              data_pool_id: value
            });
          }
        });

      }              break;

      case 'check_static': {

        if (this.type === 'rds') {
          this.toStep('check_rds')
          return
        }

        if (!this.sharedData.valid) {
          this.checkValid = true;
        } else {
          if (this.type === 'static') {
            if (!this.staticPool.valid) {
              this.checkValid = true;
            } else {
              this.toStep('done');
            }
          } else if (this.type === 'dynamic') {
            this.checkValid = false;
            this.toStep('dynamic');
          } else {
            this.checkValid = false;
            this.toStep('guest');
          }
        }
      }                    break;

      case 'check_rds': {
        if (!this.sharedData.valid) {
          this.checkValid = true;
        } else {
          if (!this.rdsPool.valid) {
            this.checkValid = true;
          } else {
            this.toStep('done');
          }
        }
      }                 break;

      case 'dynamic': {
        this.step = step;
        if (!this.poolSettings){
          this.dynamicPool.get('increase_step').setValue(1);
          this.dynamicPool.get('initial_size').setValue(1);
          this.dynamicPool.get('total_size').setValue(1);
          this.dynamicPool.get('reserve_size').setValue(1);
          this.dynamicPool.get('create_thin_clones').setValue(true);
          this.dynamicPool.get('enable_vms_remote_access').setValue(true);
          this.dynamicPool.get('start_vms').setValue(true);
          this.dynamicPool.get('set_vms_hostnames').setValue(true);
          this.warming_vm.setValue(true);
          if (this.auth_dirs.length) { this.dynamicPool.get('include_vms_in_ad').setValue(true); }
        }
        this.warming_vm.valueChanges.subscribe((value) => {

          if (value) {
            this.warming_all = true;
            this.dynamicPool.get('enable_vms_remote_access').setValue(true);
            this.dynamicPool.get('start_vms').setValue(true);
            this.dynamicPool.get('set_vms_hostnames').setValue(true);
            if (this.auth_dirs.length) { this.dynamicPool.get('include_vms_in_ad').setValue(true); }
          } else {
            this.warming_all = false;
            this.dynamicPool.get('enable_vms_remote_access').setValue(false);
            this.dynamicPool.get('start_vms').setValue(false);
            this.dynamicPool.get('set_vms_hostnames').setValue(false);
            if (this.auth_dirs.length) { this.dynamicPool.get('include_vms_in_ad').setValue(false); }
          }
        });

        this.dynamicPool.get('enable_vms_remote_access').valueChanges.subscribe((value) => {
          if (value) {
          } else {
            this.dynamicPool.get('start_vms').setValue(false);
            this.dynamicPool.get('set_vms_hostnames').setValue(false);
            if (this.auth_dirs.length) { this.dynamicPool.get('include_vms_in_ad').setValue(false); }
          }
        });

        this.dynamicPool.get('start_vms').valueChanges.subscribe((value) => {
          if (value) {
            this.dynamicPool.get('enable_vms_remote_access').setValue(true);
          } else {
            this.dynamicPool.get('set_vms_hostnames').setValue(false);
            if (this.auth_dirs.length) { this.dynamicPool.get('include_vms_in_ad').setValue(false); }
          }
        });

        this.dynamicPool.get('set_vms_hostnames').valueChanges.subscribe((value) => {
          if (value) {
            this.dynamicPool.get('enable_vms_remote_access').setValue(true);
            this.dynamicPool.get('start_vms').setValue(true);
          } else {
            if (this.auth_dirs.length) { this.dynamicPool.get('include_vms_in_ad').setValue(false); }
          }
        });

        if (this.auth_dirs.length && !this.poolSettings) {
          this.dynamicPool.get('include_vms_in_ad').valueChanges.subscribe((value) => {
            if (value) {
              this.dynamicPool.get('enable_vms_remote_access').setValue(true);
              this.dynamicPool.get('start_vms').setValue(true);
              this.dynamicPool.get('set_vms_hostnames').setValue(true);
            }
          });
        }
      }               break;

      case 'check_dynamic': {
        if (!this.dynamicPool.valid) {
          this.checkValid = true;
        } else {
          this.toStep('done');
        }
      }                     break;

      case 'guest': {
        this.step = step;
        if (!this.poolSettings){
          this.guestPool.get('increase_step').setValue(1);
          this.guestPool.get('initial_size').setValue(1);
          this.guestPool.get('total_size').setValue(1);
          this.guestPool.get('reserve_size').setValue(1);
          this.guestPool.get('vm_disconnect_action_timeout').setValue(60);
          this.guestPool.get('create_thin_clones').setValue(true);
          this.guestPool.get('is_guest').setValue(true);
          this.guestPool.get('enable_vms_remote_access').setValue(true);
          this.guestPool.get('start_vms').setValue(true);
        }

      }             break;

      case 'check_guest': {
        if (!this.guestPool.valid) {
          this.checkValid = true;
        } else {
          this.toStep('done');
        }
      }                   break;

      case 'done': {
        this.step = step;
        /* сборка данных для отправки */

        let data: any = { ...this.sharedData.value };
        let method = '';

        if (this.type === 'static') {

          data = { ...data, ...this.staticPool.value };
          method = 'addStaticPool';

        }

        if (this.type === 'rds') {

          data = { ...data, ...this.rdsPool.value };
          method = 'addRdsPool';

        }

        if (this.type === 'dynamic') {

          data = { ...data, ...this.dynamicPool.value };
          method = 'addDynamicPool';

        }

        if (this.type === 'guest') {

          data = { ...data, ...this.guestPool.value };
          method = 'addGuestPool';

        }

        this.waitService.setWait(true);

        if (this.sub) {
          this.sub.unsubscribe();
        }

        this.sub = this.addPoolService[method](data).subscribe(() => {
          this.dialogRef.close();
          this.waitService.setWait(false);
        }, () => {

          let use_step = this.last.split('_');
          if (use_step.length > 1) {
            if (use_step[1] === 'rds') {
              this.toStep('static');
            } else {
              this.toStep(use_step[1]);
            }

          } else {
            this.toStep('static');
          }
        });

      }            break;
    }
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
