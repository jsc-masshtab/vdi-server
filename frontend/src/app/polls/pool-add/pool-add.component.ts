import { WaitService } from './../../common/components/wait/wait.service';
import { VmsService } from './../../resourses/vms/vms.service';
import { TemplatesService } from './../../resourses/templates/templates.service';
import { DatapoolsService } from './../../resourses/datapools/datapools.service';
import { NodesService } from './../../resourses/nodes/nodes.service';
import { ClustersService } from './../../resourses/clusters/clusters.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit,ViewChild,ViewContainerRef } from '@angular/core';
import { Validators } from '@angular/forms';
import { PoolsService } from '../pools.service';
import { map } from 'rxjs/operators';
import { trigger, style, animate, transition } from "@angular/animations";
import { 
	FormBuilder, 
	FormGroup
} from '@angular/forms';

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

export class PoolAddComponent implements OnInit {

  public templates: object[] = [];
  public clusters: object[] = [];
  public nodes: object[] = [];
  public datapools: object[] = [];
  public vms: object[] = [];
  private finishPoll:{} = {};

  public id_cluster:string;
  public id_node:string;
  public id_datapool:string;
  public id_template:string;

  public chooseTypeForm: FormGroup;
  public createPoolForm:FormGroup;

  public pending:object = {
    clusters: false,
    nodes: false,
    datapools: false,
    vms: false,
    templates: false
  };

  public error:boolean = false;

  public data: {} = {};
  public table_field:{} = [];
  public step:string = 'chooseType';

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


  @ViewChild("selectNodeRef") selectNodeRef: ViewContainerRef;
  @ViewChild("selectDatapoolRef") selectDatapoolRef: ViewContainerRef;
  @ViewChild("selectVmRef") selectVmRef: ViewContainerRef;


  constructor(private poolsService: PoolsService,
              private clustersService: ClustersService,
              private nodesService: NodesService,
              private datapoolsService: DatapoolsService,
              private templatesService:TemplatesService,
              private vmsService: VmsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<PoolAddComponent>,
              private fb: FormBuilder) {}

  ngOnInit() {
    this.createChooseTypeForm(); 
  }

  private createChooseTypeForm(): void {
		this.chooseTypeForm = this.fb.group({
			type: "Статический"
    });   
  }

  private createDinamicPoolInit(): void {
    this.createPoolForm = this.fb.group({
      "name": ['', Validators.required],
      "template_id": ['', Validators.required],
      "cluster_id": ['', Validators.required],
      "node_id":['', Validators.required],
      "datapool_id": ['', Validators.required],
      "initial_size": ['', Validators.required],
      "reserve_size": ['', Validators.required],
      "total_size": ['', Validators.required]
    });
    this.finishPoll = {};
    this.getTemplate();
    this.getClusters();
  }

  private createStaticPoolInit(): void {
    this.createPoolForm = this.fb.group({
      "name": ['', Validators.required],
      "cluster_id": ['', Validators.required],
      "node_id": ['', Validators.required],
      "datapool_id": ['', Validators.required],
      "vm_ids_list": [[], Validators.required]
    });
    this.finishPoll = {};
    this.getClusters();
  }

  
  private getTemplate() {
    this.pending['templates'] = true;
    this.templatesService.getAllTemplates().valueChanges.pipe(map(data => data.data.controllers)).subscribe((data) => {
      let entity = this.parseEntity(data,'templates');

      this.templates = entity.map((item) => {
        let parse = JSON.parse(item['info']);
        return {
          'id': parse.id,
          'verbose_name': parse.verbose_name
        }
      });
      this.pending['templates'] = false;
    },(error) => {
      this.pending['templates'] = false;
    });
  }

  private getClusters() {
    this.pending['clusters'] = true;
    this.clustersService.getAllClusters().valueChanges.pipe(map(data => data.data.controllers)) // подумать об выборе запрашиваемых полей
      .subscribe( (data) => {
        this.clusters = this.parseEntity(data,'clusters');
        this.pending['clusters'] = false;
      },
      (error)=> {
        this.pending['clusters'] = false;
        this.clusters = [];
    });
  }

  private getNodes(id_cluster) {
    this.pending['nodes'] = true;
    this.nodesService.getAllNodes(id_cluster).valueChanges.pipe(map(data => data.data.controllers))
      .subscribe( (data) => {
        this.nodes = this.parseEntity(data,'nodes');
        this.pending['nodes'] = false;
      },
      (error)=> {
        this.nodes = [];
        this.pending['nodes'] = false;
      });
  }

  private getDatapools(id_node) {
    this.pending['datapools'] = true;
    this.datapoolsService.getAllDatapools(id_node).valueChanges.pipe(map(data => data.data.controllers))
    .subscribe( (data) => {
      this.datapools = this.parseEntity(data,'datapools');
      this.pending['datapools'] = false;
    },
    (error) => {
      this.pending['datapools'] = false;
      this.datapools = [];
    });
  }

  private getVms() {
    this.pending['vms'] = true;
    this.vmsService.getAllVms(this.id_cluster,this.id_node,this.id_datapool).valueChanges.pipe(map(data => data.data.list_of_vms))
    .subscribe( (data) => {
      this.vms =  data;
      this.pending['vms'] = false;
    },
    (error)=> {
      this.vms = [];
      this.pending['vms'] = false;
    });
  }

  private parseEntity(data:[],prop): object[] {
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

  public selectTemplate(value:object) {
    this.id_template = value['value'].id;
    this.finishPoll['template_name'] = value['value']['verbose_name'];
    this.createPoolForm.get('template_id').setValue(this.id_template);
  }

  public selectCluster(value:object) {
    this.id_cluster = value['value'].id;
    this.finishPoll['cluster_name'] = value['value']['verbose_name'];
    this.nodes = [];
    this.datapools = [];
    this.vms = [];
    this.id_node = ""; // скрыть пулы
    this.id_datapool = ""; // скрыть вм
   
    this.createPoolForm.get('cluster_id').setValue(this.id_cluster);

    if(this.selectNodeRef) {
      this.selectNodeRef['value'] = "";
    }

    this.getNodes(this.id_cluster);
  }

  public selectNode(value:object) {
    this.id_node = value['value'].id;
    this.finishPoll['node_name'] = value['value']['verbose_name'];
    this.id_datapool = ""; // скрыть вм
    this.datapools = [];
    this.vms = [];
  
    this.createPoolForm.get('node_id').setValue(this.id_node);
   
    if(this.selectDatapoolRef) {
      this.selectDatapoolRef['value'] = "";
    }
    
    this.getDatapools(this.id_node);
  }

  public selectDatapool(value:object) {
    this.id_datapool = value['value'].id;
    this.finishPoll['datapool_name'] = value['value']['verbose_name'];
    this.vms = [];

    this.createPoolForm.get('datapool_id').setValue(this.id_datapool);

    if(this.selectVmRef) {
      this.selectVmRef['value'] = "";
    }
    this.getVms();
  }

  public selectVm(value:[]) {
    let id_vms: [] = [];
    id_vms = value['value'].map(vm => vm['id']);
    this.createPoolForm.get('vm_ids_list').setValue(id_vms);
    this.finishPoll['vm_name'] = value['value'].map(vm => vm['name']);
  }

  private resetLocalData():void {
    this.clusters = [];
    this.nodes = [];
    this.datapools = [];
    this.vms = [];
    this.id_cluster = "";
    this.id_node = "",
    this.id_datapool = "";
  }

  private chooseCollection(): void {
    if(this.chooseTypeForm.value.type === 'Динамический') {
     this.table_field = [
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
          property: "template_name"
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
      this.table_field = [
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
    if(this.createPoolForm.status === "INVALID") {
      let timer;
      this.error = true;
      if(!timer) {
        timer = setTimeout(() => {
          this.error = false;
        },3000);
      }
      return false;
    }
    return true;
  }

  public send(step:string) {
    if(step === 'chooseType') {
      this.step = 'chooseType';

      this.steps[1].completed = false;
      this.steps[2].completed = false;

      this.resetLocalData();
      
      if(this.createPoolForm) {
        this.createPoolForm.reset();
      }
    }

    if(step === 'createPool') {
      this.step = 'createPool';
      this.error = false;

      this.steps[1].completed = true;
      this.steps[2].completed = false;
   
      this.resetLocalData();

      if(this.chooseTypeForm.value.type === 'Динамический') {
        this.createDinamicPoolInit();
      }

      if(this.chooseTypeForm.value.type === 'Статический') {
        this.createStaticPoolInit();
      }
    }

    if(step === 'finish-see') {

      if(this.createPoolForm) {
        let validPrev: boolean = this.handlingValidForm();
  
        if(!validPrev) return;
  
        this.chooseCollection();

        let value = this.createPoolForm.value;
  
        if(this.chooseTypeForm.value.type === 'Динамический') {
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

    if(step === 'finish-ok') {
      let value = this.createPoolForm.value;
      this.waitService.setWait(true);
     
      if(this.chooseTypeForm.value.type === 'Динамический') {
        
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
              this.poolsService.getAllPools().subscribe();
              this.dialogRef.close();
              this.waitService.setWait(false);
            });
      } 

      if(this.chooseTypeForm.value.type === 'Статический') {
        
        this.poolsService.createStaticPool(
                                value.name,
                                value.cluster_id,
                                value.node_id,
                                value.datapool_id,
                                value.vm_ids_list)
            .subscribe(() => { 
              this.poolsService.getAllPools().subscribe();
              this.dialogRef.close();
              this.waitService.setWait(false);
            });
      } 
    } 
  }

  ngOnDestroy() {
    if(this.createPoolForm) {
      this.createPoolForm.reset();
    }
  }
}
