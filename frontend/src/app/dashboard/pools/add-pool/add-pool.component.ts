import { PoolsUpdateService } from './../all-pools/pools.update.service';
import { WaitService } from '../../common/components/single/wait/wait.service';

import { AddPoolService } from './add-pool.service';

import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { Validators } from '@angular/forms';
import { map } from 'rxjs/operators';
import { trigger, style, animate, transition } from '@angular/animations';
import { FormBuilder, FormGroup } from '@angular/forms';
import { Subscription } from 'rxjs';

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

export class PoolAddComponent {

  sub: Subscription

  public checkValid: boolean = false;
  public error: boolean = false;

  public type: string = 'static';
  public step: string;
  public last: string;

  public data: any;

  public sharedData: FormGroup;
  public staticPool: FormGroup;
  public dynamicPool: FormGroup;

  constructor(
    private updatePools: PoolsUpdateService,
    private addPoolService: AddPoolService,
    private dialogRef: MatDialogRef<PoolAddComponent>,
    private fb: FormBuilder,
    private waitService: WaitService) {}

  ngOnInit() {
    this.initForms()
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

  initForms() {

    this.sharedData = this.fb.group({
      verbose_name: ['', [Validators.required, Validators.pattern(/^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$/)]],
      connection_types: [[], Validators.required],

      controller_id: ['', Validators.required],
      cluster_id: ['', Validators.required],
      node_id: ['', Validators.required],
      datapool_id: ['', Validators.required]
    });

    this.staticPool = this.fb.group({
      vms: [[], Validators.required]
    });

    this.dynamicPool = this.fb.group({
      template_id: ['', Validators.required],
      vm_name_template: ['', [Validators.required, Validators.pattern(/^([a-zA-Z]+[a-zA-Z0-9-]*){0,63}$/)]],
      ad_cn_pattern: [''],
      increase_step: ['', [Validators.required, Validators.max(200), Validators.min(1)]],
      reserve_size: ['', [Validators.required, Validators.max(200), Validators.min(1)]],
      initial_size: [0, [Validators.required, Validators.max(200), Validators.min(1)]],
      total_size: ['', [Validators.required, Validators.max(10000), Validators.min(1)]],

      create_thin_clones: true,
      prepare_vms: true,
    }, { validators: this.totalSizeValidator() });

    this.toStep('type');
  }

  getData(type, data: any = {}) {

    /* комбинирует запросы с разными фильтрами от одной точки входа controllers */

    this.addPoolService.getData(type, data).valueChanges.pipe(map(data => data.data.controller[type])).subscribe((res) => {
      this.data[type] = res
    })
  }

  resetData() {
    this.data = {
      connection_types: ['RDP', 'NATIVE_RDP', 'SPICE', 'SPICE_DIRECT'],
      controllers: [],
      clusters: [],
      nodes: [],
      datapools: [],
      vms: [],
      templates: []
    }
  }

  public toStep(step: string) {
    this.last = this.step
    this.step = step

    /* Обработка каждого шага */

    switch (step) {
      case 'type': {

        /* Установка начальных занчений */

        this.resetData();
        this.checkValid = false;
        this.sharedData.reset();
        this.staticPool.reset();
        this.dynamicPool.reset();

      } break;

      case 'static': {
        /* Выбор первого типа */

        if (!this.sharedData.get('connection_types').value) this.sharedData.get('connection_types').setValue([this.data['connection_types'][0]])

        /* Запрос на контроллеры */

        this.addPoolService.getData('controllers').valueChanges.pipe(map(data => data.data['controllers'])).subscribe((res) => {
          this.data['controllers'] = res

          if (!this.sharedData.get('controller_id').value) this.sharedData.get('controller_id').setValue(this.data['controllers'][0]['id'])
        })

        /* Подписка на изменение полей формы для отправки запросов на сервер */

        this.sharedData.controls['controller_id'].valueChanges.subscribe((value) => {
          this.sharedData.controls['cluster_id'].reset() // Очистка поля под текущим

          if (value) this.getData('clusters', { "id_": value }) // запрос данных для выборки в очищенном поле
        })

        this.sharedData.controls['cluster_id'].valueChanges.subscribe((value) => {
          this.sharedData.controls['node_id'].reset()

          if (value) this.getData('nodes', {
            "id_": this.sharedData.get('controller_id').value,
            "cluster_id": value
          })
        })

        this.sharedData.controls['node_id'].valueChanges.subscribe((value) => {
          this.sharedData.controls['datapool_id'].reset()

          if (value) this.getData('data_pools', {
            "id_": this.sharedData.get('controller_id').value,
            "cluster_id": this.sharedData.get('cluster_id').value,
            "node_id": value
          })
        })

        this.sharedData.controls['datapool_id'].valueChanges.subscribe((value) => {
          this.staticPool.controls['vms'].reset()

          if (value) this.getData('vms', {
            "id_": this.sharedData.get('controller_id').value,
            "cluster_id": this.sharedData.get('cluster_id').value,
            "node_id": this.sharedData.get('node_id').value,
            "data_pool_id": value
          })

          this.dynamicPool.controls['template_id'].reset()

          if (value) this.getData('templates', {
            "id_": this.sharedData.get('controller_id').value,
            "cluster_id": this.sharedData.get('cluster_id').value,
            "node_id": this.sharedData.get('node_id').value,
            "data_pool_id": value
          })
        })
      } break;

      case 'check_static': {
        if (!this.sharedData.valid) {
          this.checkValid = true
          this.toStep('static')
        } else {
          if (this.type == 'static') {
            if (!this.staticPool.valid) {
              this.checkValid = true
              this.toStep('static')
            } else {
              this.toStep('done')
            }
          } else {
            this.checkValid = false
            this.toStep('dynamic')
          }
        }
      } break;

      case 'dynamic': {
        this.dynamicPool.get('create_thin_clones').setValue(true)
        this.dynamicPool.get('prepare_vms').setValue(true)
      } break;

      case 'check_dynamic': {
        if (!this.dynamicPool.valid) {
          this.checkValid = true
          this.toStep('dynamic')
        } else {
          this.toStep('done')
        }
      } break;

      case 'done': {

        /* сборка данных для отправки */

        let data: any = { ...this.sharedData.value }
        let method = ''

        if (this.type == 'static') {

          data = { ...data, ...this.staticPool.value }
          method = 'addStaticPool'

        }

        if (this.type == 'dynamic') {

          data = { ...data, ...this.dynamicPool.value }
          method = 'addDynamicPool'

        }

        this.waitService.setWait(true);

        if (this.sub) {
          this.sub.unsubscribe()
        }

        this.sub = this.addPoolService[method](data).subscribe(() => {
          this.dialogRef.close();
          this.updatePools.setUpdate('update');
          this.waitService.setWait(false);
        }, () => {
          this.toStep(this.last)
        })

      } break;
    }
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe()
    }
  }
}
