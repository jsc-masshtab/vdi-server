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
    },
    {
      title: 'Кластеры',
      icon: 'building',
      route: 'resourses/clusters'
    }
  ];

  public spinner:boolean = true;


  constructor(private service: NodesService,private activatedRoute: ActivatedRoute,private router: Router){}

  ngOnInit() {
    this.collectionAction();

    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.id_cluster = param.get('id') as string;
      console.log(param);
      this.getNodes(this.id_cluster);

      this.crumbs.push(
        {
          title: 'Серверы',
          icon: 'server',
          route: `resourses/clusters/${this.id_cluster}/nodes`
        }
      );

    });
  }

  private getNodes(id_cluster) {
    this.service.getAllNodes(id_cluster).valueChanges.pipe(map(data => data.data.nodes))
      .subscribe( (data) => {
        this.nodes = data;
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
    console.log(event);
    this.router.navigate([`resourses/clusters/${event.cluster.id}/nodes/${event.id}`]);
  }
}
