import { Component, OnInit } from '@angular/core';
import { NodesService } from './nodes.service';
import { map } from 'rxjs/operators';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';

@Component({
  selector: 'vdi-nodes',
  templateUrl: './nodes.component.html',
  styleUrls: ['./nodes.component.scss']
})


export class NodesComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [];
  public nodes: {};
  private id_cluster:string;

  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    }
  ];

  public spinner:boolean = true;


  constructor(private service: NodesService,private activatedRoute: ActivatedRoute,private router: Router){}

  ngOnInit() {
    this.collectionAction();

    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.id_cluster = param.get('id') as string;

      this.getNodes(this.id_cluster);
    });
  }

  private getNodes(id_cluster) {
    this.service.getAllNodes(id_cluster).valueChanges.pipe(map(data => data.data.nodes))
      .subscribe( (data) => {
        this.nodes = data;
        if(this.id_cluster) {
          this.crumbs.push( {                                                // переход в имя кластера - серверы     // можно хранить в глобальном стейте ?
            title: `Кластер ${this.nodes[0]['cluster']['verbose_name']}`,
            icon: 'building',
            route: `resourses/clusters/${this.nodes[0]['cluster']['id']}`
          },
          {
            title: 'Серверы',
            icon: 'server',
           // route: `resourses/clusters/${this.id_cluster}/nodes`
          })
        } else {                                                                         // переход из общего меню серверы
          this.crumbs.push({
            title: 'Серверы',
            icon: 'server',
           // route: `resourses/nodes`
          })
        }
   
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

  public collectionAction(): void {
    this.collection = [
      {
        title: 'Название',
        property: 'verbose_name'
      },
      {
        title: 'Локация',
        property: "datacenter_name"
      },
      {
        title: 'IP-адрес',
        property: 'management_ip'
      },
      {
        title: 'CPU',
        property: 'cpu_count'
      },
      {
        title: 'RAM',
        property: 'memory_count'
      },
      {
        title: 'Статус',
        property: 'status'
      }
    ];
  }

  public routeTo(event): void {
    localStorage.setItem('node_name',event['verbose_name']);
    localStorage.setItem('node_id',event['id']);
    localStorage.setItem('cluster_name',event['cluster']['verbose_name']);
    localStorage.setItem('cluster_id',event['cluster']['id']);

    if(this.id_cluster) { // переход в имя кластера - серверы 
      this.router.navigate([`resourses/clusters/${event.cluster.id}/nodes/${event.id}/datapools`]);
    } else {             // переход из общего меню серверы
      this.router.navigate([`resourses/nodes/${event.id}/datapools`]);
    }
  }
}
