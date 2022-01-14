import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { StatisticsService } from './statistics.service';


@Component({
  selector: 'vdi-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss'],
})
export class StatisticsComponent implements OnInit {
  public readonly months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
  public readonly years = [2018, 2019, 2020, 2021, 2022];

  public year = new FormControl(new Date().getFullYear());
  public month = new FormControl('all');

  constructor(private statisticsService: StatisticsService){}

  ngOnInit(): void {
    
      this.statisticsService.getStatistics().subscribe((res)=>{
        console.log(res);
        
      },
      (error) => {                              //Error callback
        console.error('error caught in component')
        console.log(error);
      })
  }
  public chosenYearHandler() {
   
  }

  public chosenMonthHandler() {
    
  }

  public refresh(): void {
   
  }


  
}
