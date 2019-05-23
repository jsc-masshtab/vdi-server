import { Component, OnInit } from '@angular/core';
import { map } from 'rxjs/operators';
import { PoolsService } from './polls.service';
import { PoolAddComponent } from './pool-add/pool-add.component';

import { MatDialog } from '@angular/material';

@Component({
  selector: 'vdi-polls',
  templateUrl: './polls.component.html',
  styleUrls: ['./polls.component.scss']
})

export class PollsComponent implements OnInit {

  public pools: [];
  public spinner:boolean = true;

  public collection: object[] = [
    {
      title: '№',
      property: 'index'
    },
    {
      title: 'Название',
      property: 'name'
    },
    {
      title: 'Начальный размер пула',    // всего вм
      property: 'settings',
      property_lv2: 'initial_size'
    },
    {
      title: 'Размер пула',      // сколько свободных осталось
      property: 'settings',
      property_lv2: 'reserve_size'
    },
    {
      title: 'Состояние',
      property: 'state',
      property_lv2: 'running'
    }
  ];

  public crumbs: object[] = [
    {
      title: 'Пулы виртуальных машин',
      icon: 'desktop'
    }
  ];

  constructor(private service: PoolsService,public dialog: MatDialog){}

  ngOnInit() {
    this.getAllPools();
  }

  public openCreatePool() {
    this.dialog.open(PoolAddComponent, {
      width: '500px'
    });
  }

  private getAllPools() {
    this.service.getAllPools().valueChanges.pipe(map(data => data.data.pools))
      .subscribe( (data) => {
        this.pools = data;
        this.spinner = false;
      },
      (error)=> {
        this.spinner = false;
      });
  }

}
