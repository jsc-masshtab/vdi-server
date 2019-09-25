import { AddPoolService } from './add-pool.service';
import { WaitService } from '../../common/components/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit, ViewChild, ViewContainerRef, OnDestroy } from '@angular/core';
import { Validators } from '@angular/forms';
import { PoolsService } from '../pools.service';
import { map } from 'rxjs/operators';
import { trigger, style, animate, transition } from '@angular/animations';
import { FormBuilder, FormGroup } from '@angular/forms';

import { IFinishPoolView, IFinishPoolForm, IPendingAdd, ISelectValue } from '../definitions/pools';

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
  private key: string = 'value';

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

  @ViewChild('selectNodeRef') selectNodeRef: ViewContainerRef;
  @ViewChild('selectDatapoolRef') selectDatapoolRef: ViewContainerRef;
  @ViewChild('selectVmRef') selectVmRef: ViewContainerRef;

  constructor(private poolsService: PoolsService,
              private addPoolService: AddPoolService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<PoolAddComponent>,
              private fb: FormBuilder) {}

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
      name: ['', Validators.required],
      template_id: ['', Validators.required],
      cluster_id: ['', Validators.required],
      node_id: ['', Validators.required],
      datapool_id: ['', Validators.required],
      initial_size: ['', Validators.required],
      reserve_size: ['', Validators.required],
      total_size: ['', Validators.required]
    });
    this.finishPoolView = {};
    this.getControllers();
  }

  private createStaticPoolInit(): void {
    this.createPoolForm = this.fb.group({
      name: ['', Validators.required],
      cluster_id: ['', Validators.required],
      node_id: ['', Validators.required],
      datapool_id: ['', Validators.required],
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
    this.addPoolService.getAllTemplates(ipController).valueChanges.pipe(map(data => data.data.controller.templates)).subscribe((data) => {
      this.templates = data.map((item) => {
        const parse = JSON.parse(item.info);
        return {
          id: parse.id,
          verbose_name: parse.verbose_name
        };
      });
      this.pending.templates = false;
    }, () => {
      this.pending.templates = false;
    });
  }

  private getClusters(ipController?: string): void  {
    this.pending.clusters = true;
    this.addPoolService.getAllClusters(ipController).valueChanges.pipe(map(data => data.data))
      .subscribe( (data) => {
        if (ipController) {
          this.clusters = data.controller.clusters;
        } else {
          this.clusters = this.parseEntity(data.controllers, 'clusters');
        }
        this.pending.clusters = false;
      },
      () => {
        this.pending.clusters = false;
        this.clusters = [];
    });
  }

  private getNodes(idCluster): void  {
    this.pending.nodes = true;
    this.addPoolService.getAllNodes(idCluster).valueChanges.pipe(map(data => data.data.controllers))
      .subscribe( (data) => {
        this.nodes = this.parseEntity(data, 'nodes');
        this.pending.nodes = false;
      },
      () => {
        this.nodes = [];
        this.pending.nodes = false;
      });
  }

  private getDatapools(idNode): void  {
    this.pending.datapools = true;
    this.addPoolService.getAllDatapools(idNode).valueChanges.pipe(map(data => data.data.controllers))
    .subscribe( (data) => {
      this.datapools = this.parseEntity(data, 'datapools');
      this.pending.datapools = false;
    },
    () => {
      this.pending.datapools = false;
      this.datapools = [];
    });
  }

  private getVms(): void  {
    this.pending.vms = true;
    this.addPoolService.getAllVms(this.idCluster, this.idNode, this.idDatapool).valueChanges.pipe(map(data => data.data.list_of_vms))
    .subscribe( (data) => {
      this.vms =  data;
      this.pending.vms = false;
    },
    () => {
      this.vms = [];
      this.pending.vms = false;
    });
  }

  private parseEntity(data: [], prop: string): object[] {
    let arr: [][] = [];
    this[prop] = [];
    arr = data.map(controller => controller[`${prop}`]);

    arr.forEach((arrInto: []) => {
        arrInto.forEach((obj: {}) => {
          this[prop].push(obj);
        });
    });
    return this[prop];
  }

  public selectController(value: ISelectValue): void  {
    this.ipController = value.value.ip;
    this.getTemplates(this.ipController);
    this.getClusters(this.ipController);
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

    this.createPoolForm.get('cluster_id').setValue(this.idCluster);

    if (this.selectNodeRef) {
      this.selectNodeRef[this.key] = '';
    }

    this.getNodes(this.idCluster);
  }

  public selectNode(value: ISelectValue): void  {
    this.idNode = value.value.id;
    this.finishPoolView.node_name = value.value.verbose_name;
    this.idDatapool = ''; // скрыть вм
    this.datapools = [];
    this.vms = [];
    this.createPoolForm.get('node_id').setValue(this.idNode);
    if (this.selectDatapoolRef) {
      this.selectDatapoolRef[this.key] = '';
    }
    this.getDatapools(this.idNode);
  }

  public selectDatapool(value: ISelectValue): void  {
    this.idDatapool = value.value.id;
    this.finishPoolView.datapool_name = value.value.verbose_name;
    this.vms = [];
    this.createPoolForm.get('datapool_id').setValue(this.idDatapool);
    if(this.selectVmRef) {
      this.selectVmRef[this.key] = '';
    }
    this.getVms();
  }

  public selectVm(value: []): void  {
    const keyId = 'id';
    const keyName = 'name';
    let idVms: [] = [];
    idVms = value[this.key].map(vm => vm[keyId]);
    this.createPoolForm.get('vm_ids_list').setValue(idVms);
    this.finishPoolView.vm_name = value[this.key].map(vm => vm[keyName]);
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
          property: 'type'
        },
        {
          title: 'Название',
          property: 'name'
        },
        {
          title: 'Шаблон',
          property: 'template_name'
        },
        {
          title: 'Кластер',
          property: 'cluster_name'
        },
        {
          title: 'Сервер',
          property: 'node_name'
        },
        {
          title: 'Пул данных',
          property: 'datapool_name'
        },
        {
          title: 'Начальное количество ВМ',
          property: 'initial_size'
        },
        {
          title: 'Количество создаваемых ВМ',
          property: 'reserve_size'
        },
        {
          title: 'Максимальное количество создаваемых ВМ',
          property: 'total_size'
        }
      ];
    } else {
      this.tableField = [
        {
          title: 'Тип',
          property: 'type'
        },
        {
          title: 'Название',
          property: 'name'
        },
        {
          title: 'Кластер',
          property: 'cluster_name'
        },
        {
          title: 'Сервер',
          property: 'node_name'
        },
        {
          title: 'Пул данных',
          property: 'datapool_name'
        },
        {
          title: 'Виртуальные машины',
          property: 'vm_name'
        }
      ];
    }
  }

  private handlingValidForm(): boolean {
    if (this.createPoolForm.status === 'INVALID') {
      let timer;
      this.error = true;
      if (!timer) {
        timer = setTimeout(() => {
          this.error = false;
        }, 3000);
      }
      return false;
    }
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
    const validPrev: boolean = this.handlingValidForm();
    if (!validPrev) { return; }
    this.chooseCollection();

    const formValue: Partial<IFinishPoolForm> = this.createPoolForm.value;

    if (this.chooseTypeForm.value.type === 'Автоматический') {
      this.finishPoolView.initial_size = formValue.initial_size;
      this.finishPoolView.reserve_size = formValue.reserve_size;
      this.finishPoolView.total_size = formValue.total_size;
    }
    this.finishPoolView.name = formValue.name;
    this.finishPoolView.type = this.chooseTypeForm.value.type;

    this.step = 'finish-see';
    this.steps[1].completed = true;
    this.steps[2].completed = true;
  }

  private actionFinishOk(): void  {
    const formValue: Partial<IFinishPoolForm> = this.createPoolForm.value;
    this.waitService.setWait(true);
    if (this.chooseTypeForm.value.type === 'Автоматический') {
      this.poolsService.createDinamicPool(
                              formValue.name,
                              formValue.template_id,
                              formValue.cluster_id,
                              formValue.node_id,
                              formValue.datapool_id,
                              formValue.initial_size,
                              formValue.reserve_size,
                              formValue.total_size)
        .subscribe(() => {
          this.poolsService.getAllPools().subscribe(() => {
            this.waitService.setWait(false);
          });
          this.dialogRef.close();
        });
    }

    if (this.chooseTypeForm.value.type === 'Статический') {
      this.poolsService.createStaticPool(
                              formValue.name,
                              formValue.cluster_id,
                              formValue.node_id,
                              formValue.datapool_id,
                              formValue.vm_ids_list)
        .subscribe(() => {
          this.poolsService.getAllPools().subscribe(() => {
            this.waitService.setWait(false);
          });
          this.dialogRef.close();
        });
    }
  }

  public send(step: string) {
    if (step === 'chooseType') {
      this.actionChooseType();
    }

    if (step === 'createPool') {
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
