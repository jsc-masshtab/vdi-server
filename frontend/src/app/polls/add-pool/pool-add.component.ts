import { ControllersService } from '../../settings/controllers/controllers.service';
import { WaitService } from '../../common/components/wait/wait.service';
import { VmsService } from '../../resourses/vms/vms.service';
import { TemplatesService } from '../../resourses/templates/templates.service';
import { DatapoolsService } from '../../resourses/datapools/datapools.service';
import { NodesService } from '../../resourses/nodes/nodes.service';
import { ClustersService } from '../../resourses/clusters/clusters.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit, ViewChild, ViewContainerRef, OnDestroy } from '@angular/core';
import { Validators } from '@angular/forms';
import { PoolsService } from '../pools.service';
import { map } from 'rxjs/operators';
import { trigger, style, animate, transition } from '@angular/animations';
import { FormBuilder, FormGroup } from '@angular/forms';

interface Ipending  {
  clusters: boolean;
  nodes: boolean;
  datapools: boolean;
  vms: boolean;
  templates: boolean;
  controllers: boolean;
}

@Component({
  selector: 'vdi-pool-add',
  templateUrl: './pool-add.component.html',
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
  private finishPoll: {} = {};

  public idCluster: string;
  public idNode: string;
  public idDatapool: string;
  public idTemplate: string;
  public ipController: string;

  public chooseTypeForm: FormGroup;
  public createPoolForm: FormGroup;

  public pending: Ipending = {
    clusters: false,
    nodes: false,
    datapools: false,
    vms: false,
    templates: false,
    controllers: false
  };

  public error: boolean = false;

  public data: {} = {};
  public tableField: {} = [];
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
              private clustersService: ClustersService,
              private nodesService: NodesService,
              private datapoolsService: DatapoolsService,
              private templatesService:TemplatesService,
              private vmsService: VmsService,
              private controllersService: ControllersService,
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
    this.finishPoll = {};
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
    this.finishPoll = {};
    this.getClusters();
  }

  private getControllers() {
    this.pending.controllers = true;
    this.controllersService.getAllControllers().valueChanges.pipe(map(data => data.data.controllers)).subscribe((data) => {
      this.controllers = data;
      this.pending.controllers = false;
    },() => {
      this.pending.controllers = false;
    });
  }

  private getTemplates(ipController: string) {
    this.pending.templates = true;
    this.templatesService.getAllTemplates(ipController).valueChanges.pipe(map(data => data.data.controller.templates)).subscribe((data) => {
      this.templates = data.map((item) => {
        let parse = JSON.parse(item['info']);
        return {
          'id': parse.id,
          'verbose_name': parse.verbose_name
        }
      });
      this.pending.templates = false;
    },() => {
      this.pending.templates = false;
    });
  }

  private getClusters(ipController?: string) {
    this.pending.clusters = true;
    this.clustersService.getAllClusters(ipController).valueChanges.pipe(map(data => data.data)) // подумать об выборе запрашиваемых полей
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

  private getNodes(idCluster) {
    this.pending.nodes = true;
    this.nodesService.getAllNodes(idCluster).valueChanges.pipe(map(data => data.data.controllers))
      .subscribe( (data) => {
        this.nodes = this.parseEntity(data, 'nodes');
        this.pending.nodes = false;
      },
      () => {
        this.nodes = [];
        this.pending.nodes = false;
      });
  }

  private getDatapools(idNode) {
    this.pending.datapools = true;
    this.datapoolsService.getAllDatapools(idNode).valueChanges.pipe(map(data => data.data.controllers))
    .subscribe( (data) => {
      this.datapools = this.parseEntity(data, 'datapools');
      this.pending.datapools = false;
    },
    () => {
      this.pending.datapools = false;
      this.datapools = [];
    });
  }

  private getVms() {
    this.pending.vms = true;
    this.vmsService.getAllVms(this.idCluster, this.idNode, this.idDatapool).valueChanges.pipe(map(data => data.data.list_of_vms))
    .subscribe( (data) => {
      this.vms =  data;
      this.pending.vms = false;
    },
    ()=> {
      this.vms = [];
      this.pending.vms = false;
    });
  }

  private parseEntity(data: [], prop: string): object[] {
    let arr: [][] = [];
    this[prop] = [];
    arr = data.map(controller => controller[`${prop}`]);

    arr.forEach((arr: []) => {
        arr.forEach((obj: {}) => {
          this[prop].push(obj);
        }); 
    });
    return this[prop];
  }

  public selectController(value: object) {
    this.ipController = value['value'];
    this.getTemplates(this.ipController);
    this.getClusters(this.ipController);
  }

  public selectTemplate(value:object) {
    this.idTemplate = value['value'].id;
    this.finishPoll['template_name'] = value['value']['verbose_name'];
    this.createPoolForm.get('template_id').setValue(this.idTemplate);
  }

  public selectCluster(value:object) {
    this.idCluster = value['value'].id;
    this.finishPoll['cluster_name'] = value['value']['verbose_name'];
    this.nodes = [];
    this.datapools = [];
    this.vms = [];
    this.idNode = ''; // скрыть пулы
    this.idDatapool = ''; // скрыть вм
   
    this.createPoolForm.get('cluster_id').setValue(this.idCluster);

    if(this.selectNodeRef) {
      this.selectNodeRef['value'] = '';
    }

    this.getNodes(this.idCluster);
  }

  public selectNode(value:object) {
    this.idNode = value['value'].id;
    this.finishPoll['node_name'] = value['value']['verbose_name'];
    this.idDatapool = ''; // скрыть вм
    this.datapools = [];
    this.vms = [];
    this.createPoolForm.get('node_id').setValue(this.idNode);
    if (this.selectDatapoolRef) {
      this.selectDatapoolRef['value'] = '';
    }
    this.getDatapools(this.idNode);
  }

  public selectDatapool(value: object) {
    this.idDatapool = value['value'].id;
    this.finishPoll['datapool_name'] = value['value']['verbose_name'];
    this.vms = [];
    this.createPoolForm.get('datapool_id').setValue(this.idDatapool);
    if(this.selectVmRef) {
      this.selectVmRef['value'] = '';
    }
    this.getVms();
  }

  public selectVm(value: []) {
    let id_vms: [] = [];
    id_vms = value['value'].map(vm => vm['id']);
    this.createPoolForm.get('vm_ids_list').setValue(id_vms);
    this.finishPoll['vm_name'] = value['value'].map(vm => vm['name']);
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

  private chooseCollection(): void {
    if(this.chooseTypeForm.value.type === 'Автоматический') {
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

  public send(step: string) {
    if (step === 'chooseType') {
      this.step = 'chooseType';

      this.steps[1].completed = false;
      this.steps[2].completed = false;

      this.resetLocalData();
      if (this.createPoolForm) {
        this.createPoolForm.reset();
      }
    }

    if (step === 'createPool') {
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

    if (step === 'finish-see') {

      if (this.createPoolForm) {
        const validPrev: boolean = this.handlingValidForm();
        if (!validPrev) { return; }
        this.chooseCollection();

        const value = this.createPoolForm.value;
        if (this.chooseTypeForm.value.type === 'Автоматический') {
          this.finishPoll['name'] = value.name;
          this.finishPoll['initial_size'] = value.initial_size;
          this.finishPoll['reserve_size'] = value.reserve_size;
          this.finishPoll['total_size'] = value.total_size;
          this.finishPoll['type'] = this.chooseTypeForm.value.type;
        }
        if(this.chooseTypeForm.value.type === 'Статический') {
          this.finishPoll['name'] = value.name;
          this.finishPoll['type'] = this.chooseTypeForm.value.type;
        }

        this.step = 'finish-see';
        this.steps[1].completed = true;
        this.steps[2].completed = true;
      }
    }

    if (step === 'finish-ok') {
      const value = this.createPoolForm.value;
      this.waitService.setWait(true);
      if (this.chooseTypeForm.value.type === 'Автоматический') {
        this.poolsService.createDinamicPool(
                                value.name,
                                value.template_id,
                                value.cluster_id,
                                value.node_id,
                                value.datapool_id,
                                value.initial_size,
                                value.reserve_size,
                                value.total_size)
            .subscribe(() => {
              this.poolsService.getAllPools().subscribe(() => {
                this.waitService.setWait(false);
              });
              this.dialogRef.close();
            });
      }

      if (this.chooseTypeForm.value.type === 'Статический') {
        this.poolsService.createStaticPool(
                                value.name,
                                value.cluster_id,
                                value.node_id,
                                value.datapool_id,
                                value.vm_ids_list)
            .subscribe(() => {
              this.poolsService.getAllPools().subscribe(() => {
                this.waitService.setWait(false);
              });
              this.dialogRef.close();
            });
      }
    }
  }

  ngOnDestroy() {
    if (this.createPoolForm) {
      this.createPoolForm.reset();
    }
  }
}
