import { NodesService } from './../resourses/nodes/nodes.service';
import { Component, OnInit, Input, HostBinding } from '@angular/core';
import { map } from 'rxjs/operators';

@Component({
  selector: 'vdi-resourse-into',
  templateUrl: './resourse-into.component.html',
  styleUrls: ['./resourse-into.component.scss']
})
export class ResourseIntoComponent implements OnInit {

  @Input() clusterId:string;      // входящие св-ва без пробела,переменные с _
  @Input() clusterName:string;      // входящие св-ва без пробела,переменные с _
  @Input() what:string;
  public dataTable: [];
  public collection: object[] = [];
  public spinner:boolean;
  public menuActive:string = 'servers';

  constructor(private nodesService: NodesService) {}

  ngOnInit() {
  }

  ngOnChanges() {
    if(this.clusterId && this.menuActive === 'servers') {
      this.spinner = true;
      this.nodesService.getAllNodes(this.clusterId).valueChanges.pipe(map(data => data.data.nodes)).subscribe((res) => {
        this.dataTable = res;
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
        this.spinner = false;
        console.log(res);
      },
      (error) => {
        this.spinner = false;
      });
    }
  }

}
