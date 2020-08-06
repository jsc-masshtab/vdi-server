import { PoolsUpdateService } from './../all-pools/pools.update.service';
import { WaitService } from '../../common/components/single/wait/wait.service';

import { AddPoolService } from './add-pool.service';

import { MatDialogRef } from '@angular/material';
import { Component } from '@angular/core';
import { Validators } from '@angular/forms';
import { map } from 'rxjs/operators';
import { trigger, style, animate, transition } from '@angular/animations';
import { FormBuilder, FormGroup } from '@angular/forms';

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

  public checkValid: boolean = false;
  public error: boolean = false;

  public type: string = 'static';
  public step: string;

  public data: any;
  
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

  initForms() {
    this.staticPool = this.fb.group({
      verbose_name: ['', [Validators.required, Validators.pattern(/^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$/)]],
      connection_types: [[], Validators.required],

      controller_id: ['', Validators.required],
      cluster_id: ['', Validators.required],
      node_id: ['', Validators.required],
      datapool_id: ['', Validators.required],

      vms: [[], Validators.required]
    });

    this.dynamicPool = this.fb.group({
      template_id: 0,
      increase_step: 0,

      vm_name_template: 0,
      max_vm_amount: 0,
      max_amount_of_create_attempts: 0,

      min_size: 0,
      max_size: 0,
      reserve_size: 0,
      initial_size: [0, [Validators.required, Validators.max(200), Validators.min(1)]],
      total_size: ['', [Validators.required, Validators.max(1000), Validators.min(1)]],

      create_thin_clones: false,
    });

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
      connection_types: ['SPICE', 'RDP', 'NATIVE_RDP'],
      controllers: [],
      clusters: [],
      nodes: [],
      datapools: [],
      vms: []
    }
  }

  public toStep(step: string) {

    this.step = step

    /* Обработка каждого шага */
    
    switch (step) {
      case 'type': {

        /* Установка начальных занчений */

        this.resetData();
        this.checkValid = false;
        this.staticPool.reset();
        this.dynamicPool.reset();

      } break;

      case 'create': {

        /* Запрос на контроллеры */

        this.addPoolService.getData('controllers').valueChanges.pipe(map(data => data.data['controllers'])).subscribe((res) => {
          this.data['controllers'] = res
        })

        /* Подписка на изменение полей формы  */

        this.staticPool.controls['controller_id'].valueChanges.subscribe((value) => {
          this.staticPool.controls['cluster_id'].reset()           // Очистка поля под текущим

          if (value) this.getData('clusters', { "id_": value })    // запрос данных для выборки в очищенном поле
        })

        this.staticPool.controls['cluster_id'].valueChanges.subscribe((value) => {
          this.staticPool.controls['node_id'].reset()

          if (value) this.getData('nodes', {
            "id_": this.staticPool.get('controller_id').value,
            "cluster_id": value
          })
        })

        this.staticPool.controls['node_id'].valueChanges.subscribe((value) => {
          this.staticPool.controls['datapool_id'].reset()

          if (value) this.getData('data_pools', {
            "id_": this.staticPool.get('controller_id').value,
            "cluster_id": this.staticPool.get('cluster_id').value,
            "node_id": value
          })
        })

        this.staticPool.controls['datapool_id'].valueChanges.subscribe((value) => {
          this.staticPool.controls['vms'].reset()

          if (value) this.getData('vms', {
            "id_": this.staticPool.get('controller_id').value,
            "cluster_id": this.staticPool.get('cluster_id').value,
            "node_id": this.staticPool.get('node_id').value,
            "data_pool_id": value
          })
        })
      } break;

      case 'dynamic': {

        if (!this.staticPool.valid) {

          /* вернуть назад, если не прошел валидацию */
          
          this.checkValid = true
          this.toStep('create')
        }

      } break;

      case 'done': {

        /* сборка данных для отправки */

        let data: any = { ...this.staticPool.value }

        if (this.staticPool.valid) {

          this.waitService.setWait(true);
          
          this.addPoolService.addStaticPool(data).subscribe(() => {
            this.dialogRef.close();
            this.updatePools.setUpdate('update');
            this.waitService.setWait(false);
          }, () => {
            this.dialogRef.close();
            this.updatePools.setUpdate('update');
            this.waitService.setWait(false);
          })
        } else {

          /* вернуть назад, если не пройдена валидация */

          this.checkValid = true
          this.toStep('create')
        }

      } break;
    }
  }
}
