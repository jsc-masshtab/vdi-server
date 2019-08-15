import { VmsService } from './../../resourses/vms/vms.service';
import { TemplatesService } from './../../resourses/templates/templates.service';
import { DatapoolsService } from './../../resourses/datapools/datapools.service';
import { NodesService } from './../../resourses/nodes/nodes.service';
import { ClustersService } from './../../resourses/clusters/clusters.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit,ViewChild,ViewContainerRef } from '@angular/core';
import { PoolsService } from '../pools.service';
import { map } from 'rxjs/operators';
import { 
	FormBuilder, 
	FormGroup
} from '@angular/forms';

@Component({
  selector: 'vdi-pool-add',
  templateUrl: './pool-add.component.html'
})

export class PoolAddComponent implements OnInit {

  public templates: object[] = [];
  public clusters: object[] = [];
  public nodes: object[] = [];
  public datapools: object[] = [];
  public vms: object[] = [];

  public poolName:string;
  public id_cluster:string;
  public id_node:string;
  public id_datapool:string;
  public id_template:string;


  public dinamicPoolForm: FormGroup;
  public staticPoolForm: FormGroup;
  public chooseTypeForm: FormGroup;
  public step:string = "chooseType";

  public pending:object = {
    clusters: false,
    nodes: false,
    datapools: false,
    vms: false,
    templates: false
  };

  public la;

  @ViewChild("selectNodeRef") selectNodeRef: ViewContainerRef;
  @ViewChild("selectDatapoolRef") selectDatapoolRef: ViewContainerRef;
  @ViewChild("selectVmRef") selectVmRef: ViewContainerRef;


  constructor(private poolsService: PoolsService,
              private clustersService: ClustersService,
              private nodesService: NodesService,
              private datapoolsService: DatapoolsService,
              private templatesService:TemplatesService,
              private vmsService: VmsService,
              private dialogRef: MatDialogRef<PoolAddComponent>,
              private fb: FormBuilder) {}

  ngOnInit() {
    this.createChooseTypeForm();
  }

  private createChooseTypeForm(): void {
		this.chooseTypeForm = this.fb.group({
			type: ""
    });   
  }

  private createDinamicPoolInit(): void {
    this.dinamicPoolForm = this.fb.group({
      "name": "",
      "template_id": "",
      "cluster_id": "",
      "node_id": "",
      "datapool_id": "",
      "initial_size": "",
      "reserve_size": ""
    });
    this.getTemplate();
    this.getClusters();
  }

  private createStaticPoolInit(): void {
    this.staticPoolForm = this.fb.group({
      "name": "",
      "cluster_id": "",
      "node_id": "",
      "datapool_id": "",
      "vm_ids_list": [],
    });
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
    this.id_template = value['value'];
    this.dinamicPoolForm.get('template_id').setValue(this.id_template);
  }

  public selectCluster(value:object) {
    console.log('select Cluster');
    this.id_cluster = value['value'];
    this.datapools = [];
    this.vms = [];
    this.id_node = "",
    this.id_datapool = "";
    if(this.dinamicPoolForm) {
      this.dinamicPoolForm.get('cluster_id').setValue(this.id_cluster);
    }
    if(this.staticPoolForm) {
      this.staticPoolForm.get('cluster_id').setValue(this.id_cluster);
    }

    this.getNodes(this.id_cluster);
    if(this.selectNodeRef) {
      this.selectNodeRef['value'] = "";
    }
  }

  public selectNode(value:object) {
    console.log('select Node');
    this.id_node = value['value'];
    this.id_datapool = "";
    this.datapools = [];
    this.vms = [];
    if(this.dinamicPoolForm) {
      this.dinamicPoolForm.get('node_id').setValue(this.id_node);
    }
    if(this.staticPoolForm) {
      this.staticPoolForm.get('node_id').setValue(this.id_node);
    }
    if(this.selectDatapoolRef) {
      this.selectDatapoolRef['value'] = "";
    }
    
    this.getDatapools(this.id_node);
  }

  public selectDatapool(value:object) {
    console.log('select Datapools');
    this.id_datapool = value['value'];
    this.vms = [];
    if(this.dinamicPoolForm) {
      this.dinamicPoolForm.get('datapool_id').setValue(this.id_datapool);
    }
    if(this.staticPoolForm) {
      this.staticPoolForm.get('datapool_id').setValue(this.id_datapool);
    }
    if(this.selectVmRef) {
      this.selectVmRef['value'] = "";
    }
    this.getVms();
  }

  public selectVm(value:object) {
    if(this.staticPoolForm) {
      this.staticPoolForm.get('vm_ids_list').setValue(value["value"]);
    }
    console.log('select vms',value); 
  }

  public send(step:string) {
  
    if(step === 'chooseType') {
      this.step = 'chooseType';
      this.id_cluster = "";
      this.id_node = "",
      this.id_datapool = "";
      this.clusters = [];
      this.nodes = [];
      this.datapools = [];
      this.vms = [];
      
      if(this.staticPoolForm) {
        this.staticPoolForm.reset();
      }
      if(this.dinamicPoolForm) {
        this.dinamicPoolForm.reset();
      }
    }

    if(step === 'createPool') {
      this.step = 'createPool';
      if(this.chooseTypeForm.value.type === 'Динамический') {
        console.log(this.step,this.chooseTypeForm.value.type);
        this.createDinamicPoolInit();
        this.la = 'Динамический';
      }

      if(this.chooseTypeForm.value.type === 'Статический') {
        this.createStaticPoolInit();
        this.la = 'Статический';
      }
    }

    if(step === 'finish') {
      if(this.chooseTypeForm.value.type === 'Динамический') {
        console.log(this.dinamicPoolForm.value);
      }  else {
        console.log(this.staticPoolForm.value);
      }
      
    }
    // let createPoolForm_value = this.createPoolForm.value;

    // this.poolsService.createPoll(createPoolForm_value.name,
    //                             createPoolForm_value.template_id,
    //                             createPoolForm_value.cluster_id,
    //                             createPoolForm_value.node_id,
    //                             createPoolForm_value.datapool_id,
    //                             createPoolForm_value.initial_size,
    //                             createPoolForm_value.reserve_size)
    //   .subscribe((res) => {
    //     if(res) {
    //       this.poolsService.getAllPools().subscribe();
    //       this.dialogRef.close();
    //     }
    // });
  }

  ngOnDestroy() {
    if(this.staticPoolForm) {
      this.staticPoolForm.reset();
    }
    if(this.dinamicPoolForm) {
      this.dinamicPoolForm.reset();
    }
  }

}
