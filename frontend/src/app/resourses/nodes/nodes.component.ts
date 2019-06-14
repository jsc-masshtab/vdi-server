import { Component, OnInit } from '@angular/core';
import { NodesService } from './nodes.service';
import { map } from 'rxjs/operators';
import { Router } from '@angular/router';

@Component({
  selector: 'vdi-nodes',
  templateUrl: './nodes.component.html',
  styleUrls: ['./nodes.component.scss']
})


export class NodesComponent implements OnInit {

  public infoTemplates: [];
  public collection: object[] = [
    {
      title: '№',
      property: 'index'
    },
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

  public nodes: {};
  public crumbs: object[] = [
    {
      title: 'Ресурсы',
      icon: 'database'
    },
    {
      title: 'Серверы',
      icon: 'server'
    }
  ];

  public spinner:boolean = false;

  constructor(private service: NodesService,private router: Router){}

  ngOnInit() {
    this.getNodes();
  }

  private getNodes() {
    this.spinner = true;
    this.service.getAllNodes().valueChanges.pipe(map(data => data.data.nodes))
      .subscribe( (data) => {
        this.nodes = data;
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

  public routeTo(event): void {
    this.router.navigate([`resourses/nodes/${event.id}`]);
  }
}
