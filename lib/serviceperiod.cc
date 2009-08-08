#include <string.h>
#include <assert.h>
#include "serviceperiod.h"
#include "defuns.h"

using namespace std;


static time_t get_time_t(int tm_mday, int tm_mon, int tm_year)
{
    struct tm t;
    t.tm_sec = 0;
    t.tm_min = 0;
    t.tm_hour = 0;
    t.tm_mday = tm_mday;
    t.tm_mon = tm_mon;
    t.tm_year = tm_year;
    t.tm_wday = -1;
    t.tm_yday = -1;
    t.tm_isdst = -1;

    return mktime(&t);
}


ServicePeriodException::ServicePeriodException(int32_t _tm_mday, int32_t _tm_mon, 
                                               int32_t _tm_year)
{
    tm_mday = _tm_mday;
    tm_mon = _tm_mon;
    tm_year = _tm_year;
}


ServicePeriodException::ServicePeriodException()
{
    tm_mday = 0;
    tm_mon = 0;
    tm_year = 0;
}


ServicePeriod::ServicePeriod(std::string _id, int32_t _start_mday, 
                             int32_t _start_mon, int32_t _start_year, 
                             int32_t _end_mday, int32_t _end_mon, 
                             int32_t _end_year, int32_t _duration, 
                             bool _weekday, bool _saturday, 
                             bool _sunday)
{
    id = _id;

    start_time = get_time_t(_start_mday, _start_mon, _start_year);
    end_time = get_time_t(_end_mday, _end_mon, _end_year);

    duration = _duration;
    weekday = _weekday; 
    saturday = _saturday;
    sunday = _sunday;
}


ServicePeriod::ServicePeriod(const ServicePeriod &s) 
{
    id = s.id;

    start_time = s.start_time;
    end_time = s.end_time; 

    duration = s.duration;
    weekday = s.weekday; 
    saturday = s.saturday;
    sunday = s.sunday;
}


ServicePeriod::ServicePeriod()
{
    // blank service period object
    start_time = 0;
    end_time = 0;

    duration = 0;
    weekday = false; 
    saturday = false;
    sunday = false;
}


ServicePeriod::ServicePeriod(FILE *fp)
{
    char _id[MAX_ID_LEN];
    assert(fread(_id, 1, MAX_ID_LEN, fp) == MAX_ID_LEN);
    id = _id;

    assert(fread(&start_time, sizeof(time_t), 1, fp) == 1);
    assert(fread(&end_time, sizeof(time_t), 1, fp) == 1);

    assert(fread(&duration, sizeof(int32_t), 1, fp) == 1);
    assert(fread(&weekday, sizeof(bool), 1, fp) == 1);
    assert(fread(&saturday, sizeof(bool), 1, fp) == 1);
    assert(fread(&sunday, sizeof(bool), 1, fp) == 1);

    uint32_t num_exceptions_on;
    assert(fread(&num_exceptions_on, sizeof(uint32_t), 1, fp) == 1);
    for (int i=0; i < num_exceptions_on; i++)
    {
        ServicePeriodException e;
        assert(fread(&e, sizeof(ServicePeriodException), 1, fp) == 1);
        add_exception_on(e.tm_mday, e.tm_mon, e.tm_year);
    }

    uint32_t num_exceptions_off;
    assert(fread(&num_exceptions_off, sizeof(uint32_t), 1, fp) == 1);
    for (int i=0; i < num_exceptions_off; i++)
    {
        ServicePeriodException e;
        assert(fread(&e, sizeof(ServicePeriodException), 1, fp) == 1);
        add_exception_off(e.tm_mday, e.tm_mon, e.tm_year);
    }
}


void ServicePeriod::write(FILE *fp)
{
    char spstr[MAX_ID_LEN];
    strncpy(spstr, id.c_str(), MAX_ID_LEN);
    assert(fwrite(spstr, sizeof(char), MAX_ID_LEN, fp) == MAX_ID_LEN);

    assert(fwrite(&start_time, sizeof(time_t), 1, fp) == 1);
    assert(fwrite(&end_time, sizeof(time_t), 1, fp) == 1);

    assert(fwrite(&duration, sizeof(int32_t), 1, fp) == 1);
    assert(fwrite(&weekday, sizeof(bool), 1, fp) == 1);
    assert(fwrite(&saturday, sizeof(bool), 1, fp) == 1);
    assert(fwrite(&sunday, sizeof(bool), 1, fp) == 1);

    uint32_t num_exceptions_on = exceptions_on.size();
    assert(fwrite(&num_exceptions_on, sizeof(uint32_t), 1, fp) == 1);
    for (vector<ServicePeriodException>::iterator i = exceptions_on.begin();
         i != exceptions_on.end(); i++)
        assert(fwrite(&(*i), sizeof(ServicePeriodException), 1, fp) == 1);

    uint32_t num_exceptions_off = exceptions_off.size();
    assert(fwrite(&num_exceptions_off, sizeof(uint32_t), 1, fp) == 1);
    for (vector<ServicePeriodException>::iterator i = exceptions_off.begin();
         i != exceptions_off.end(); i++)
        assert(fwrite(&(*i), sizeof(ServicePeriodException), 1, fp) == 1);
}


void ServicePeriod::add_exception_on(int32_t tm_mday, int32_t tm_mon, int32_t tm_year)
{
    exceptions_on.push_back(ServicePeriodException(tm_mday, tm_mon, tm_year));
}


void ServicePeriod::add_exception_off(int32_t tm_mday, int32_t tm_mon, int32_t tm_year)
{
    exceptions_off.push_back(ServicePeriodException(tm_mday, tm_mon, tm_year));
}


bool ServicePeriod::is_turned_on(int32_t tm_mday, int32_t tm_mon, int32_t tm_year)
{
    for (vector<ServicePeriodException>::iterator i = exceptions_on.begin();
         i != exceptions_on.end(); i++)
    {
        if ((*i).tm_mday == tm_mday && (*i).tm_mon == tm_mon && 
            (*i).tm_year == tm_year)
            return true;
    }

    return false;
}


bool ServicePeriod::is_turned_off(int32_t tm_mday, int32_t tm_mon, int32_t tm_year)
{
    for (vector<ServicePeriodException>::iterator i = exceptions_off.begin();
         i != exceptions_off.end(); i++)
    {
        if ((*i).tm_mday == tm_mday && (*i).tm_mon == tm_mon && 
            (*i).tm_year == tm_year)
            return true;
    }

    return false;
}
