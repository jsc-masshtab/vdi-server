import { WaitService } from '../../common/components/single/wait/wait.service';

import { AddPoolService } from './add-pool.service';

import { MatDialogRef } from '@angular/material';
import { Component, OnInit, ViewChild, ViewContainerRef, OnDestroy } from '@angular/core';
import { Validators } from '@angular/forms';
import { PoolsService } from '../all-pools/pools.service';
import { map } from 'rxjs/operators';
import { trigger, style, animate, transition } from '@angular/animations';
import { FormBuilder, FormGroup } from '@angular/forms';

import { IFinishPoolView, IFinishPoolForm, IPendingAdd, ISelectValue } from './definitions/add-pool';

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

  public templates: object[] = [];
  public clusters: object[] = [];
  public nodes: object[] = [];
  public datapools: object[] = [];
  public vms: object[] = [];
  public controllers: object[] = [];
  private finishPoolView: Partial<IFinishPoolView>;

  public idCluster: string;
  public idNode: string;
  public idDatapool: string;
  public idTemplate: string;
  public ipController: string;

  public chooseTypeForm: FormGroup;
  public createPoolForm: FormGroup;

  public pending: IPendingAdd = {
    clusters: false,
    nodes: false,
    datapools: false,
    vms: false,
    templates: false,
    controllers: false
  };

  public error: boolean = false;

  public tableField: object[];
  public step: string = 'chooseType';

  public steps = [
    {
      type: 'chooseType',
      completed: true,
      disabled: false
    },
    {
      type: 'createPool',
      completed: false,
      disabled: true
    },
    {
      type: 'finish-see',
      completed: false,
      disabled: true
    }
  ];

  public checkValid: boolean = false;
  private create_thin_clones: boolean = false;

  @ViewChild('selectNodeRef') selectNodeRef: ViewContainerRef;
  @ViewChild('selectDatapoolRef') selectDatapoolRef: ViewContainerRef;
  @ViewChild('selectVmRef') selectVmRef: ViewContainerRef;

  constructor(private poolsService: PoolsService,
              private addPoolService: AddPoolService,
              private dialogRef: MatDialogRef<PoolAddComponent>,
              private fb: FormBuilder,
              private waitService: WaitService) {}

  ngOnInit() {
    this.createChooseTypeForm();
  }

  private createChooseTypeForm(): void {
    this.chooseTypeForm = this.fb.group({
      type: 'Статический'
    });
  }

  private createDinamicPoolInit(): void {
    this.createPoolForm = this.fb.group({
      verbose_name: ['', [Validators.required, Validators.pattern(/^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$/)]],
      template_id: ['', Validators.required],
      cluster_id: ['', Validators.required],
      node_id: ['', Validators.required],
      datapool_id: ['', Validators.required],
      reserve_size: ['', [Validators.required, Validators.max(200), Validators.min(1)]],
      vm_name_template: ['', [Validators.required, Validators.pattern(/^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$/)]],
      controller_ip: ['', Validators.required],
      size: this.fb.group({
        initial_size: ['', [Validators.required, Validators.max(200), Validators.min(1)]],
        total_size: ['', [Validators.required, Validators.max(1000), Validators.min(1)]],
      }, {validators: this.totalSizeValidator()}),
      create_thin_clones: this.create_thin_clones});
    this.finishPoolView = {};
    this.getControllers();
  }

  private createStaticPoolInit(): void {
    this.createPoolForm = this.fb.group({
      verbose_name: ['', [Validators.required,  Validators.pattern(/^[а-яА-ЯёЁa-zA-Z0-9]+[а-яА-ЯёЁa-zA-Z0-9.-_+ ]*$/)]],
      vm_ids_list: [[], Validators.required]
    });
    this.finishPoolView = {};
    this.getClusters();
  }

  private getControllers(): void  {
    this.pending.controllers = true;
    this.addPoolService.getAllControllers().valueChanges.pipe(map(data => data.data.controllers)).subscribe((data) => {
      this.controllers = data;
      this.pending.controllers = false;
    }, () => {
      this.pending.controllers = false;
    });
  }

  private getTemplates(ipController: string): void  {
    this.pending.templates = true;
    this.addPoolService.getAllTemplates(ipController).valueChanges.pipe(map(data => data.data.templates)).subscribe((data) => {
      this.templates = data;
      this.pending.templates = false;
    }, () => {
      this.pending.templates = false;
    });
  }

  private getClusters(ipController?: string): void  {
    this.pending.clusters = true;
    this.addPoolService.getAllClusters(ipController).valueChanges.pipe(map(data => data.data.clusters))
      .subscribe( (data) => {
        this.clusters = data;
        this.pending.clusters = false;
      },
      () => {
        this.pending.clusters = false;
        this.clusters = [];
    });
  }

  private getNodes(idCluster): void  {
    this.pending.nodes = true;
    this.addPoolService.getAllNodes(idCluster).valueChanges.pipe(map(data => data.data.nodes))
      .subscribe( (data) => {
        this.nodes = data;
        this.pending.nodes = false;
      },
      () => {
        this.nodes = [];
        this.pending.nodes = false;
      });
  }

  private getDatapools(idNode): void  {
    this.pending.datapools = true;
    this.addPoolService.getAllDatapools(idNode).valueChanges.pipe(map(data => data.data.datapools))
    .subscribe( (data) => {
      this.datapools = data;
      this.pending.datapools = false;
    },
    () => {
      this.pending.datapools = false;
      this.datapools = [];
    });
  }

  private getVms(): void  {
    this.pending.vms = true;
    this.addPoolService.getAllVms(this.idCluster, this.idNode, this.idDatapool).valueChanges.pipe(map(data => data.data.vms))
    .subscribe( (data) => {
      this.vms =  data;
      this.pending.vms = false;
    },
    () => {
      this.vms = [];
      this.pending.vms = false;
    });
  }

  public selectController(value: ISelectValue): void  {
    this.ipController = value.value.address;
    this.getTemplates(this.ipController);
    this.getClusters(this.ipController);
    this.createPoolForm.get('controller_ip').setValue(this.ipController);
  }

  public selectTemplate(value: ISelectValue): void  {
    this.idTemplate = value.value.id;
    this.finishPoolView.template_name = value.value.verbose_name;
    this.createPoolForm.get('template_id').setValue(this.idTemplate);
  }

  public selectCluster(value: ISelectValue): void  {
    this.idCluster = value.value.id;
    this.finishPoolView.cluster_name = value.value.verbose_name;
    this.nodes = [];
    this.datapools = [];
    this.vms = [];
    this.idNode = ''; // скрыть пулы
    this.idDatapool = ''; // скрыть вм

    if (this.chooseTypeForm.value.type === 'Автоматический') {
      this.createPoolForm.get('cluster_id').setValue(this.idCluster);
    }

    if (this.selectNodeRef) {
      this.selectNodeRef['value'] = '';
    }

    this.getNodes(this.idCluster);
  }

  public selectNode(value: ISelectValue): void  {
    this.idNode = value.value.id;
    this.finishPoolView.node_name = value.value.verbose_name;
    this.idDatapool = ''; // скрыть вм
    this.datapools = [];
    this.vms = [];

    if (this.chooseTypeForm.value.type === 'Автоматический') {
      this.createPoolForm.get('node_id').setValue(this.idNode);
    }

    if (this.selectDatapoolRef) {
      this.selectDatapoolRef['value'] = '';
    }
    this.getDatapools(this.idNode);
  }

  public selectDatapool(value: ISelectValue): void  {
    this.idDatapool = value.value.id;
    this.finishPoolView.datapool_name = value.value.verbose_name;
    this.vms = [];

    if (this.chooseTypeForm.value.type === 'Автоматический') {
      this.createPoolForm.get('datapool_id').setValue(this.idDatapool);
    }

    if (this.selectVmRef) {
      this.selectVmRef['value'] = '';
    }

    if (this.chooseTypeForm.value.type === 'Статический') {
      this.getVms();
    }
  }

  public selectVm(value: []): void {
    let idVms: [] = [];
    idVms = value['value'].map(vm => vm['id']);
    this.createPoolForm.get('vm_ids_list').setValue(idVms);
    this.finishPoolView.vm_name = value['value'].map(vm => vm['verbose_name']);
  }

  private resetLocalData(): void {
    this.controllers = [];
    this.clusters = [];
    this.nodes = [];
    this.datapools = [];
    this.vms = [];
    this.ipController = '';
    this.idCluster = '';
    this.idNode = '',
    this.idDatapool = '';
  }

  private chooseCollection() {
    if (this.chooseTypeForm.value.type === 'Автоматический') {
     this.tableField = [
        {
          title: 'Тип',
          property: 'type',
          type: 'string'
        },
        {
          title: 'Название',
          property: 'verbose_name',
          type: 'string'
        },
        {
          title: 'Тонкие клоны',
          property: 'create_thin_clones',
          type: {
            typeDepend: 'boolean',
            propertyDepend: ['Создаются', 'Не создаются']
          }
        },
        {
          title: 'Шаблон',
          property: 'template_name',
          type: 'string'
        },
        {
          title: 'Кластер',
          property: 'cluster_name',
          type: 'string'
        },
        {
          title: 'Сервер',
          property: 'node_name',
          type: 'string'
        },
        {
          title: 'Пул данных',
          property: 'datapool_name',
          type: 'string'
        },
        {
          title: 'Начальное количество ВМ',
          property: 'initial_size',
          type: 'string'
        },
        {
          title: 'Количество создаваемых ВМ',
          property: 'reserve_size',
          type: 'string'
        },
        {
          title: 'Максимальное количество создаваемых ВМ',
          property: 'total_size',
          type: 'string'
        },
        {
          title: 'Имя шаблона для ВМ',
          property: 'vm_name_template',
          type: 'string'
        }
      ];
    } else {
      this.tableField = [
        {
          title: 'Тип',
          property: 'type',
          type: 'string'
        },
        {
          title: 'Название',
          property: 'verbose_name',
          type: 'string'
        },
        {
          title: 'Кластер',
          property: 'cluster_name',
          type: 'string'
        },
        {
          title: 'Сервер',
          property: 'node_name',
          type: 'string'
        },
        {
          title: 'Виртуальные машины',
          property: 'vm_name',
          type: 'string'
        }
      ];
    }
  }

  public changeCheck(e) {
    this.create_thin_clones = e.checked;
  }

  private totalSizeValidator() {
    return (group: FormGroup) => {
      if (group.controls['total_size'].value < group.controls['initial_size'].value) {
        return {maxLessInitial: true};
      }
    };
  }

  private checkValidCreatePoolForm(): boolean {
    if (this.createPoolForm.status === 'INVALID') {
      this.checkValid = true;
      return false;
    }
    this.checkValid = false;
    return true;
  }

  private actionChooseType(): void {
    this.step = 'chooseType';

    this.steps[1].completed = false;
    this.steps[2].completed = false;

    this.resetLocalData();
    if (this.createPoolForm) {
      this.createPoolForm.reset();
    }
  }

  private actionCreatePool(): void {
    this.step = 'createPool';
    this.error = false;

    this.steps[1].completed = true;
    this.steps[2].completed = false;
    this.resetLocalData();

    if (this.chooseTypeForm.value.type === 'Автоматический') {
      this.createDinamicPoolInit();
    }

    if (this.chooseTypeForm.value.type === 'Статический') {
      this.createStaticPoolInit();
    }
  }

  private actionFinishSee(): void  {
    const validPrev: boolean = this.checkValidCreatePoolForm();
    if (!validPrev) { return; }
    this.chooseCollection();

    const formValue: Partial<IFinishPoolForm> = this.createPoolForm.value;

    if (this.chooseTypeForm.value.type === 'Автоматический') {
      this.finishPoolView.initial_size = formValue.size.initial_size;
      this.finishPoolView.reserve_size = formValue.reserve_size;
      this.finishPoolView.total_size = formValue.size.total_size;
      this.finishPoolView.vm_name_template = formValue.vm_name_template;
      this.finishPoolView.create_thin_clones = formValue.create_thin_clones;
    }
    this.finishPoolView.verbose_name = formValue.verbose_name;
    this.finishPoolView.type = this.chooseTypeForm.value.type;

    this.step = 'finish-see';
    this.steps[1].completed = true;
    this.steps[2].completed = true;
  }

  private actionFinishOk(): void  {
    const formValue: Partial<IFinishPoolForm> = this.createPoolForm.value;
    this.waitService.setWait(true);
    if (this.chooseTypeForm.value.type === 'Автоматический') {
      this.addPoolService.createDinamicPool(
                              formValue.verbose_name,
                              formValue.template_id,
                              formValue.cluster_id,
                              formValue.node_id,
                              formValue.datapool_id,
                              formValue.size.initial_size,
                              formValue.reserve_size,
                              formValue.size.total_size,
                              formValue.vm_name_template,
                              formValue.controller_ip,
                              formValue.create_thin_clones)
        .subscribe(() => {
          this.dialogRef.close();
          this.poolsService.paramsForGetPools.spin = true;
          this.poolsService.getAllPools().subscribe();
        });
    }

    if (this.chooseTypeForm.value.type === 'Статический') {
      this.addPoolService.createStaticPool(
                              formValue.verbose_name,
                              formValue.vm_ids_list)
        .subscribe(() => {
          this.dialogRef.close();
          this.poolsService.paramsForGetPools.spin = true;
          this.poolsService.getAllPools().subscribe();
        });
    }
  }

  public send(step: string) {
    if (step === 'chooseType') {
      this.checkValid = false;
      this.actionChooseType();
    }

    if (step === 'createPool') {
      this.checkValid = false;
      this.actionCreatePool();
    }

    if (step === 'finish-see') {
      this.actionFinishSee();
    }

    if (step === 'finish-ok') {
      this.actionFinishOk();
    }
  }

  ngOnDestroy() {
    if (this.createPoolForm) {
      this.createPoolForm.reset();
    }
  }
}