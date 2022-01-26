import {  Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { ApolloQueryResult } from 'apollo-client';
import { ApiResponse, IDate, StatisticsService } from './statistics.service';
import { saveAs } from 'file-saver'


@Component({
  selector: 'vdi-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.scss'],
})
export class StatisticsComponent implements OnInit {
  @ViewChild('myDiv') myDiv: ElementRef;
  public readonly months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
  public readonly years = [2018, 2019, 2020, 2021, 2022];

  public year = new FormControl('all');
  public month = new FormControl('all');
  public report: string;

  constructor(private statisticsService: StatisticsService){}

  ngOnInit(): void {
    this.generateReport()
  }

  public refresh(): void {
    this.generateReport()
  }

  public generateReport(): void {
    const params: IDate = {};
    
    if (this.month.value !== 'all'){
      params.month = this.month.value;
    }

    if (this.year.value !== 'all'){
      params.year = this.year.value;
    }

    this.statisticsService.getStatistics(params).valueChanges.subscribe( (res: ApolloQueryResult<ApiResponse>) => {
      this.report = res.data.statisticsReport;
      this.disableLinks()
      
      let iframe = document.createElement('iframe');
      iframe.width = '100%';
      iframe.height = '100%';
      iframe.srcdoc = this.report;
      
      this.myDiv.nativeElement.innerHTML = '';
      this.myDiv.nativeElement.appendChild(iframe);
    })
  }
  
  public downloadReport(): void {
    const filename = 'report.html'  
    const blob = new Blob([this.report], {
      type: 'text/plain;charset=utf-8'
    });

    saveAs(blob, filename)
  } 

  private disableLinks(): void {
    this.report += '<style type="text/css">a { pointer-events: none;}</style>'    
  }
}
