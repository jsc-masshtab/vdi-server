import { DatapoolsService } from './../../resourses/datapools/datapools.service';
import { NodesService } from './../../resourses/nodes/nodes.service';
import { ClustersService } from './../../resourses/clusters/clusters.service';
import { MatDialogRef } from '@angular/material';
import { Component, OnInit } from '@angular/core';
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

  public templates: object[];
  public clusters: object[];
  public nodes: object[];
  public datapools: object[];
  public poolName:string;
  public id_cluster:string;
  public id_node:string;
  public defaultDataTemplates:string = "Загрузка шаблонов...";
  public defaultDataClusters:string = "Загрузка кластеров...";
  public defaultDataNodes:string = "Загрузка кластеров...";
  public defaultDataPools:string = "Загрузка пулов...";
  private createPoolForm: FormGroup;


  constructor(private poolsService: PoolsService,
              private clustersService: ClustersService,
              private nodesService: NodesService,
              private datapoolsService: DatapoolsService,
              private dialogRef: MatDialogRef<PoolAddComponent>,
              private fb: FormBuilder) {}

  ngOnInit() {
    this.initForm();
    this.getTemplate();
    this.getClusters();
  }

  private initForm(): void {
		this.createPoolForm = this.fb.group({
			"name": "",
      "template_id": "",
      "cluster_id": "",
      "node_id": "",
      "datapool_id": "",
      "initial_size": "",
      "reserve_size": ""
		});
	}

  private getTemplate() {
    this.defaultDataTemplates = "Загрузка шаблонов...";
    this.poolsService.getAllTemplates().valueChanges.pipe(map(data => data.data.templates)).subscribe((res)=> {
      this.defaultDataTemplates = "- нет доступных шаблонов -";
      console.log(res);
      this.templates = res.map((item) => {
        let parse = JSON.parse(item['info']);
        return {
          'output': parse.id,
          'input': parse.verbose_name
        }
      })
    },(error) => {
      this.defaultDataTemplates = "- нет доступных шаблонов -";
    });
  }

  private getClusters() {
    this.defaultDataClusters = "Загрузка кластеров...";
    this.clustersService.getAllClusters().valueChanges.pipe(map(data => data.data.clusters))
      .subscribe( (res) => {
        this.defaultDataClusters = "- нет доступных кластеров -";
        this.clusters = res.map((item) => {
          return {
            'output': item.id,
            'input': item.verbose_name
          }
        });
      },
      (error)=> {
        this.defaultDataClusters = "- нет доступных кластеров -";
      });
  }

  private getNodes(id_cluster) {
    this.defaultDataNodes = "Загрузка серверов...";
    this.nodesService.getAllNodes(id_cluster).valueChanges.pipe(map(data => data.data.nodes))
      .subscribe( (res) => {
        this.defaultDataNodes = "- нет доступных серверов -";
        this.nodes =  res.map((item) => {
          return {
            'output': item.id,
            'input': item.verbose_name
          }
        });
      },
      (error)=> {
        this.defaultDataNodes = "- нет доступных серверов -";
      });
  }

  private getDatapools(id_node) {
    this.defaultDataPools = "Загрузка пулов...";
    this.datapoolsService.getAllDatapools(id_node).valueChanges.pipe(map(data => data.data.datapools))
    .subscribe( (res) => {
      this.defaultDataPools = "- нет доступных пулов -";
      this.datapools =  res.map((item) => {
        return {
          'output': item.id,
          'input': item.verbose_name
        }
      });
    },
    (error)=> {
      this.defaultDataPools = "- нет доступных пулов -";
    });
  }

  private selectValue(data,type: string) {

    if(type === 'template') {
      this.createPoolForm.get('template_id').setValue(data[0]);
    }

    if(type === 'cluster') {
      setTimeout(()=> {
        this.id_cluster = data[0];
        this.createPoolForm.get('cluster_id').setValue(this.id_cluster);
        this.getNodes(this.id_cluster);
      },0);
    }

    if(type === 'node') {
      setTimeout(()=> {
        this.id_node = data[0];
        this.createPoolForm.get('node_id').setValue(this.id_node);
        this.getDatapools(this.id_node);
      },0)
    }

    if(type === 'datapool') {
      this.createPoolForm.get('datapool_id').setValue(data[0]);
    }
    
  }

  public send() {
    let createPoolForm_value = this.createPoolForm.value;

    this.poolsService.createPoll(createPoolForm_value.name,
                                createPoolForm_value.template_id,
                                createPoolForm_value.cluster_id,
                                createPoolForm_value.node_id,
                                createPoolForm_value.datapool_id,
                                createPoolForm_value.initial_size,
                                createPoolForm_value.reserve_size)
      .subscribe((res) => {
        if(res) {
          this.poolsService.getAllPools().subscribe();
          this.dialogRef.close();
        }
    });
  }

}
